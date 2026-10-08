"""Cloud-only M0 source -> matching binaries -> audited portable candidate.

Only Python's standard library is used by the orchestration and its tests.
No compiler, editor or tool bootstrap belongs in the player's distribution.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

from build_support import (ROOT, LOCK, BUNDLE, REPORTS, read_json, write_json, digest,
                           run, download, extract, stage_source, copy_licenses)


def input_hash(root=ROOT):
    h = hashlib.sha256()
    paths = [root / "build/dependencies.lock.json", root / "build/config/windows.json",
             root / "tools/ci/engine_recipe.py", root / "tools/ci/build_support.py"]
    for folder in ["native", "build/patches"]:
        paths.extend(p for p in (root / folder).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        h.update(path.relative_to(root).as_posix().encode() + b"\0")
        h.update(path.read_bytes() + b"\0")
    return h.hexdigest()


def legacy_identity(root=ROOT):
    """One explicit migration, never a fuzzy restore of unrelated native code."""
    path = root / "build/native-cache-migration.json"
    if path.exists():
        migration = read_json(path)
        if migration["native_key"] == input_hash(root):
            return migration["legacy_engine_inputs"]
    return None


def setup():
    from engine_recipe import setup as install_toolchain
    install_toolchain()


def build():
    from engine_recipe import build as compile_engine
    compile_engine()


def verify_bundle():
    manifest = read_json(BUNDLE / "manifest.json")
    if manifest["engine_inputs"] != input_hash() and (not legacy_identity() or manifest["engine_inputs"] != legacy_identity()):
        raise RuntimeError("Stale engine bundle")
    expected = set(manifest["files"])
    actual = {p.relative_to(BUNDLE).as_posix() for p in BUNDLE.rglob("*")
              if p.is_file() and p != BUNDLE / "manifest.json"}
    if actual != expected:
        raise RuntimeError("Unexpected or missing engine bundle files")
    for name, expected_hash in manifest["files"].items():
        path = (BUNDLE / name).resolve()
        if not path.is_relative_to(BUNDLE.resolve()) or digest(path) != expected_hash:
            raise RuntimeError(f"Corrupt bundle entry: {name}")
    return manifest


def imported_dlls(output):
    if not re.search(r"Machine:\s+IMAGE_FILE_MACHINE_AMD64\s+\(0x8664\)", output):
        raise RuntimeError("Expected a Windows x86-64 PE file")
    names = set(re.findall(r"^\s*Name:\s+(\S+\.dll)\s*$", output, re.MULTILINE | re.IGNORECASE))
    if not names:
        raise RuntimeError("PE import inspection returned no DLLs")
    return {name.lower() for name in names}


def is_system_dll(name):
    allowed = set(read_json(ROOT / "build/config/windows-system-dlls.json"))
    return name.lower() in allowed or bool(re.fullmatch(r"api-ms-win-crt-[a-z0-9-]+\.dll", name.lower()))


def audit(directory):
    inspector = BUNDLE / "audit-tools/llvm-readobj.exe"
    inventory = {p.name.lower(): p for p in directory.iterdir() if p.suffix.lower() in [".exe", ".dll"]}
    result = {}
    for name, path in inventory.items():
        output = run([inspector, "--file-headers", "--coff-imports", path], "imports-" + name)
        imports = imported_dlls(output)
        missing = {dll for dll in imports if not is_system_dll(dll) and dll not in inventory}
        if missing:
            raise RuntimeError(f"Unbundled non-system imports in {name}: {sorted(missing)}")
        result[name] = sorted(imports)
    write_json(REPORTS / "dependency-audit.json", result)


def self_test(executable, label, cwd, offline=False):
    with tempfile.TemporaryDirectory(prefix="cairn-test-data-") as temp:
        env = os.environ.copy()
        env["APPDATA"] = temp
        env["LOCALAPPDATA"] = temp
        env["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
        args = [executable, "--headless", "--", "--self-test"]
        if offline:
            rule = "Cairn-M0-offline-" + label
            script = ROOT / "tools/ci/offline_test.ps1"
            powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
            firewall = [powershell, "-NoProfile", "-File", script,
                        "-Executable", executable, "-RuleName", rule]
            # Run the game directly so a timeout kills it and still removes the rule.
            try:
                run([*firewall, "-Mode", "block"], label + "-block-network", timeout=60)
                output = run(args, label, cwd=cwd, env=env, timeout=60)
            finally:
                run([*firewall, "-Mode", "remove"], label + "-restore-network", timeout=60)
        else:
            output = run(args, label, cwd=cwd, env=env, timeout=60)
        records = [line.split("CAIRN_SELF_TEST=", 1)[1] for line in output.splitlines() if "CAIRN_SELF_TEST=" in line]
        if len(records) != 1 or "SCRIPT ERROR:" in output or "ERROR:" in output:
            raise RuntimeError(f"{label}: missing self-test report or engine error; see log")
        report = json.loads(records[0])
        if not report.get("passed") or report.get("identity", {}).get("engine_inputs") != read_json(BUNDLE / "manifest.json")["engine_inputs"]:
            raise RuntimeError(f"{label}: self-test identity or result failed")
        if report.get("game_commit") != os.environ["GITHUB_SHA"]:
            raise RuntimeError("Game pack belongs to another commit")
        write_json(REPORTS / (label + ".json"), report)


def prepare():
    manifest = verify_bundle()
    game = ROOT / "game"
    templates = ROOT / "build/templates"
    templates.mkdir(exist_ok=True)
    for kind in ["debug", "release"]:
        shutil.copy2(BUNDLE / ("template_" + kind + ".exe"), templates / ("windows_" + kind + ".exe"))
    info = {key: manifest[key] for key in ["engine_inputs", "godot_commit", "voxel_commit"]}
    info.update({"game_commit": os.environ["GITHUB_SHA"], "milestone": "M1",
                 "native_source_key": input_hash(),
                 "ci_run": f'https://github.com/{os.environ["GITHUB_REPOSITORY"]}/actions/runs/{os.environ["GITHUB_RUN_ID"]}',
                 "target_performance": "not_run", "renderer": "gl_compatibility",
                 "engine_binaries": {key: value for key, value in manifest["files"].items() if key.endswith(".exe")}})
    write_json(game / "build_info.json", info)
    editor = BUNDLE / "editor.exe"
    output = run([editor, "--headless", "--path", game, "--import"], "editor-import", timeout=300)
    if "SCRIPT ERROR:" in output or "ERROR:" in output:
        raise RuntimeError("Project import reported errors")
    # Check each new dependency directly: a derived benchmark test can otherwise
    # report only an unresolved base class and hide the originating parse error.
    for script in ("benchmark_frame_slack", "benchmark_frame_slack_tests", "benchmark_frame_slack_runtime", "m1_frontier_preparation", "m1_frontier_boundary_runtime", "m1_frontier_edit_runtime", "benchmark"):
        output = run([editor, "--headless", "--path", game, "--check-only", "--script",
                      "res://scripts/" + script + ".gd"], "parse-" + script, timeout=60)
        if "SCRIPT ERROR:" in output or "ERROR:" in output:
            raise RuntimeError("Direct frame/benchmark parser check reported errors")
    # Run the title/self-test through the matching editor, then both actual export templates.
    self_test(editor, "editor-self-test", game)
    output = run([editor, "--headless", "--path", game, "--script", "res://scripts/m1_native_tests.gd"],
                 "m1-native-mesher-tests", timeout=120)
    if "CAIRN_M1_NATIVE=" not in output or "SCRIPT ERROR:" in output or "ERROR:" in output:
        raise RuntimeError("M1 native mesher tests failed")
    dist = ROOT / "dist"
    player = dist / "player"
    player.mkdir(parents=True, exist_ok=True)
    debug = dist / "debug-export"
    debug.mkdir(exist_ok=True)
    for mode, destination in [("debug", debug), ("release", player)]:
        output = run([editor, "--headless", "--path", game, "--export-" + mode,
                      "Windows Portable", destination / "Cairn.exe"], "export-" + mode, timeout=300)
        if "SCRIPT ERROR:" in output or "ERROR:" in output:
            raise RuntimeError("Export reported errors")
        self_test(destination / "Cairn.exe", mode + "-self-test", ROOT)
        output = run([destination / "Cairn.exe", "--headless", "--", "--m1-smoke",
                      "--m1-report-root=" + str(REPORTS / (mode + "-m1-raw"))],
                     mode + "-m1-smoke", timeout=300)
        if "CAIRN_M1_SMOKE=" not in output or "SCRIPT ERROR:" in output or "ERROR:" in output:
            # A native assertion can log an error without changing the process
            # exit code. Surface unique diagnostics in the Actions log as well
            # as retaining the full scenario log in the evidence artifact.
            errors = dict.fromkeys(line for line in output.splitlines()
                                   if "ERROR:" in line or "SCRIPT ERROR:" in line)
            print("\n".join(errors)[:8000], flush=True)
            raise RuntimeError("M1 scenario integration failed")
        output = run([destination / "Cairn.exe", "--headless", "--", "--m1-smoke", "--benchmark-mode=heavy-ab",
                      "--m1-report-root=" + str(REPORTS / (mode + "-m1-heavy-ab-raw"))],
                     mode + "-m1-heavy-ab-smoke", timeout=300)
        if "CAIRN_M1_SMOKE=" not in output or "SCRIPT ERROR:" in output or "ERROR:" in output:
            raise RuntimeError("M1 heavy A/B integration failed")
    write_json(player / "BUILD_INFO.json", info)
    shutil.copytree(BUNDLE / "LICENSES", player / "LICENSES", dirs_exist_ok=True)
    shutil.copy2(ROOT / "distribution/README.txt", player / "README.txt")
    shutil.copy2(ROOT / "distribution/NOTICE.txt", player / "LICENSES/CAIRN-NOTICE.txt")
    if (player / "Cairn.pck").read_bytes()[:4] != b"GDPC":
        raise RuntimeError("Missing or invalid Godot PCK")


def qualify():
    """Prove native registrations in all three binaries before caching them.

    Gameplay import/tests remain mandatory after this gate. A script defect must
    not discard hours of already qualified native compilation.
    """
    manifest = verify_bundle()
    project = ROOT / "build/native-qualification"
    project.mkdir(parents=True, exist_ok=True)
    (project / "project.godot").write_text(
        'config_version=5\n[application]\nrun/main_scene="res://check.tscn"\n'
        '[rendering]\nrenderer/rendering_method="gl_compatibility"\n', encoding="utf-8")
    (project / "check.tscn").write_text(
        '[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://check.gd" id="1"]\n'
        '[node name="NativeQualification" type="Node"]\nscript=ExtResource("1")\n', encoding="utf-8")
    identity = {key: manifest[key] for key in ["engine_inputs", "godot_commit", "voxel_commit"]}
    script = '''extends Node
func _ready() -> void:
    var errors: Array[String] = []
    for name_value: String in ["VoxelTerrain", "VoxelMesherBlocky", "VoxelBoxMover", "SandboxWorld", "CairnFixture", "CairnMesher", "CairnProbe", "CairnReportSink"]:
        if not ClassDB.can_instantiate(name_value): errors.append(name_value)
    if not errors.is_empty():
        push_error(str(errors))
        get_tree().quit(1)
        return
    var entry: RefCounted = ClassDB.instantiate("SandboxWorld")
    var identity: Dictionary = entry.call("get_build_identity")
    var expected: Dictionary = EXPECTED
    if identity != expected: errors.append("Native identity mismatch")
    var terrain: Node3D = ClassDB.instantiate("VoxelTerrain")
    terrain.set("generate_collisions", false)
    terrain.set("mesher", ClassDB.instantiate("VoxelMesherBlocky"))
    add_child(terrain)
    await get_tree().process_frame
    terrain.queue_free()
    await get_tree().process_frame
    print("CAIRN_SELF_TEST=" + JSON.stringify({"passed": errors.is_empty(), "errors": errors, "identity": identity, "game_commit": GAME_COMMIT}))
    get_tree().quit(0 if errors.is_empty() else 1)
'''.replace("EXPECTED", json.dumps(identity)).replace("GAME_COMMIT", json.dumps(os.environ["GITHUB_SHA"]))
    (project / "check.gd").write_text(script, encoding="utf-8")
    preset = (ROOT / "game/export_presets.cfg").read_text(encoding="utf-8")
    for mode in ["debug", "release"]:
        preset = preset.replace(f"../build/templates/windows_{mode}.exe", f"../engine-bundle/template_{mode}.exe")
    (project / "export_presets.cfg").write_text(preset, encoding="utf-8")
    editor = BUNDLE / "editor.exe"
    run([editor, "--headless", "--path", project, "--import"], "qualification-import")
    self_test(editor, "qualification-editor", project)
    for mode in ["debug", "release"]:
        target = project / mode / "Cairn.exe"
        target.parent.mkdir(exist_ok=True)
        run([editor, "--headless", "--path", project, "--export-" + mode,
             "Windows Portable", target], "qualification-export-" + mode)
        self_test(target, "qualification-" + mode, ROOT)


def package():
    verify_bundle()
    dist = ROOT / "dist"
    player = dist / "player"
    info = read_json(player / "BUILD_INFO.json")
    if info["game_commit"] != os.environ["GITHUB_SHA"] or info["engine_inputs"] != read_json(BUNDLE / "manifest.json")["engine_inputs"] or info["native_source_key"] != input_hash():
        raise RuntimeError("Prepared distribution is stale")
    audit(player)
    package_path = dist / "Cairn-windows-x86_64.zip"
    with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
        for path in sorted(player.rglob("*")):
            if path.is_file():
                zipped.write(path, path.relative_to(player).as_posix())
    if package_path.stat().st_size > 500 * 1024 * 1024:
        raise RuntimeError("Package exceeds the release size ceiling")
    # Each extraction is unique and starts without imports, tools, or developer data.
    for index, folder in enumerate(["clean", "fresh path with spaces é 世界"]):
        with tempfile.TemporaryDirectory(prefix="cairn-extraction-") as temp:
            fresh = Path(temp) / folder
            extract(package_path, fresh)
            for original in player.rglob("*"):
                if original.is_file() and digest(original) != digest(fresh / original.relative_to(player)):
                    raise RuntimeError("Extraction content differs")
            self_test(fresh / "Cairn.exe", f"extracted-offline-{index}", Path(temp), offline=True)
    (dist / "SHA256SUMS.txt").write_text(digest(package_path) + "  " + package_path.name + "\n", encoding="utf-8")
    shutil.copy2(player / "BUILD_INFO.json", dist / "BUILD_INFO.json")
    write_json(REPORTS / "candidate.json", {**info, "status": "cloud_passed_target_unverified",
               "artifact_sha256": digest(package_path), "artifact_bytes": package_path.stat().st_size,
               "render_smoke": "not_run: hosted Windows OpenGL availability is not guaranteed",
               "fog_conversion_probe": read_json(REPORTS / "m1-fog-render.json"),
               "cold_cache": os.environ.get("CAIRN_NATIVE_SOURCE") == "built",
               "native_bundle_source": os.environ.get("CAIRN_NATIVE_SOURCE", "unknown")})
    shutil.make_archive(str(dist / "Cairn-symbols"), "zip", BUNDLE / "symbols")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["key", "setup", "build", "verify", "qualify", "prepare", "package"])
    args = parser.parse_args()
    if args.command == "key":
        value = "windows-native-v2-" + input_hash()
        print(value)
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write("key=" + value + "\n")
            output.write("artifact=Cairn-native-" + value + "\n")
            output.write("legacy_key=" + ("windows-m0-" + legacy_identity() if legacy_identity() else "") + "\n")
    else:
        {"setup": setup, "build": build, "verify": verify_bundle, "qualify": qualify,
         "prepare": prepare, "package": package}[args.command]()


if __name__ == "__main__":
    main()
