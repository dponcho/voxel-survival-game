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

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "build/dependencies.lock.json"
BUNDLE = ROOT / "build/engine-bundle"
REPORTS = ROOT / "reports"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def input_hash(root=ROOT):
    h = hashlib.sha256()
    paths = [root / "build/dependencies.lock.json"]
    for folder in ["native", "build/config", "build/patches", "tools/ci"]:
        paths.extend(p for p in (root / folder).rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    for path in sorted(paths):
        h.update(path.relative_to(root).as_posix().encode() + b"\0")
        h.update(path.read_bytes() + b"\0")
    return h.hexdigest()


def run(args, label, cwd=ROOT, timeout=300, env=None):
    REPORTS.mkdir(exist_ok=True)
    args = [str(arg) for arg in args]
    started = time.monotonic()
    log = REPORTS / (label + ".log")
    print(f"Running {label}", flush=True)
    with log.open("w", encoding="utf-8") as output:
        output.write(json.dumps(args) + "\n")
        output.flush()
        try:
            result = subprocess.run(args, cwd=cwd, env=env, stdout=output,
                                    stderr=subprocess.STDOUT, timeout=timeout, check=False)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = -1
            output.write("\nTIMEOUT\n")
    with (REPORTS / "commands.jsonl").open("a", encoding="utf-8") as output:
        output.write(json.dumps({"command": args, "label": label, "exit_code": code,
                                 "seconds": round(time.monotonic() - started, 3)}) + "\n")
    if code:
        print(log.read_text(encoding="utf-8", errors="replace")[-18000:])
        raise RuntimeError(f"{label} failed with exit code {code}")
    return log.read_text(encoding="utf-8", errors="replace")


def download(spec, name):
    dest = ROOT / "build/downloads" / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or digest(dest) != spec["sha256"]:
        partial = dest.with_suffix(dest.suffix + ".partial")
        with urllib.request.urlopen(spec["url"], timeout=120) as source, partial.open("wb") as target:
            shutil.copyfileobj(source, target)
        if digest(partial) != spec["sha256"]:
            raise RuntimeError(f"Integrity failure: {name}")
        partial.replace(dest)
    return dest


def extract(archive, destination):
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zipped:
        for item in zipped.infolist():
            name = item.filename.replace("\\", "/")
            target = (destination / name).resolve()
            if not target.is_relative_to(destination.resolve()) or ":" in name:
                raise RuntimeError("Archive path escapes extraction directory")
            if (item.external_attr >> 16) & 0o170000 == 0o120000:
                raise RuntimeError("Archive symlinks are not supported")
        zipped.extractall(destination)


def stage_source(spec, name, target):
    marker = target / ".cairn-source-sha256"
    if marker.exists() and marker.read_text() == spec["sha256"]:
        return
    if target.exists():
        raise RuntimeError(f"Unrecognized staged source at {target}; use a fresh cloud workspace")
    archive = download(spec, name + ".zip")
    with tempfile.TemporaryDirectory(dir=ROOT / "build") as temp:
        extract(archive, Path(temp))
        children = list(Path(temp).iterdir())
        if len(children) != 1 or not children[0].is_dir():
            raise RuntimeError("Expected a single source archive root")
        shutil.copytree(children[0], target)
    marker.write_text(spec["sha256"])


def setup():
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.name != "nt":
        raise RuntimeError("Development setup/build runs only on Windows GitHub Actions")
    lock = read_json(LOCK)
    if sys.version.split()[0] != lock["python"]:
        raise RuntimeError("Python version differs from dependency lock")
    compiler = ROOT / "build/toolchain" / lock["compiler"]["version"]
    if not compiler.exists():
        extract(download(lock["compiler"], "compiler.zip"), compiler.parent)
    wheel = download(lock["scons"], "scons-4.9.1-py3-none-any.whl")
    run([sys.executable, "-m", "pip", "install", "--no-deps", "--no-index", str(wheel)], "setup-scons")
    compiler_bin = compiler / "bin"
    with open(os.environ["GITHUB_PATH"], "a", encoding="utf-8") as stream:
        stream.write(str(compiler_bin) + "\n")
    with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as stream:
        stream.write("CAIRN_COMPILER=" + str(compiler) + "\n")
    text = run([compiler_bin / "clang++.exe", "--version"], "compiler-identity")
    write_json(REPORTS / "toolchain.json", {"compiler": text, "python": sys.version,
               "compiler_archive_sha256": lock["compiler"]["sha256"],
               "runner_image": os.environ.get("ImageVersion", "unknown")})


def copy_licenses(source, destination):
    for path in source.rglob("*"):
        if path.is_file() and any(word in path.name.lower() for word in ["license", "licence", "copyright", "copying", "notice"]):
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def build():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("Compilation belongs in GitHub Actions")
    lock = read_json(LOCK)
    config = read_json(ROOT / "build/config/windows.json")
    engine = ROOT / "engine-src"
    stage_source(lock["godot"], "godot", engine)
    stage_source(lock["voxel"], "voxel", engine / "modules/voxel")
    module = engine / "modules/sandbox_world"
    shutil.copytree(ROOT / "native/sandbox_world", module, dirs_exist_ok=True)
    identity = {"engine_inputs": input_hash(), "godot_commit": lock["godot"]["commit"],
                "voxel_commit": lock["voxel"]["commit"]}
    (module / "build_identity.gen.h").write_text(
        "#pragma once\n" + "\n".join(f'#define CAIRN_{key.upper()} "{value}"'
                                    for key, value in identity.items()) + "\n", encoding="utf-8")
    patches = sorted((ROOT / "build/patches").rglob("*.patch"))
    if patches:
        raise RuntimeError("Downstream patches require an explicit application and verification step")
    BUNDLE.mkdir(parents=True, exist_ok=True)
    for target in config["targets"]:
        run([sys.executable, "-m", "SCons", *config["flags"], f"target={target}",
             "mingw_prefix=" + os.environ["CAIRN_COMPILER"], f'-j{config["jobs"]}'],
            "build-" + target, cwd=engine, timeout=15000)
        candidates = [p for p in (engine / "bin").glob(f"godot.windows.{target}.x86_64*.exe")
                      if not p.name.endswith(".console.exe")]
        if len(candidates) != 1:
            raise RuntimeError(f"Ambiguous {target} output: {candidates}")
        shutil.copy2(candidates[0], BUNDLE / (target + ".exe"))
    symbols = BUNDLE / "symbols"
    symbols.mkdir(exist_ok=True)
    for path in (engine / "bin").iterdir():
        if path.suffix in [".debug", ".debugsymbols", ".pdb"]:
            shutil.copy2(path, symbols / path.name)
    if not list(symbols.iterdir()):
        raise RuntimeError("Separate symbols were not produced")
    copy_licenses(engine, BUNDLE / "LICENSES/godot")
    # The compiler's static C/C++ runtime notices also travel with the game.
    copy_licenses(Path(os.environ["CAIRN_COMPILER"]), BUNDLE / "LICENSES/llvm-mingw")
    manifest = {**identity, "lock": lock, "config": config,
                "toolchain": read_json(REPORTS / "toolchain.json"),
                "files": {p.relative_to(BUNDLE).as_posix(): digest(p)
                          for p in sorted(BUNDLE.rglob("*")) if p.is_file() and p.name != "manifest.json"}}
    write_json(BUNDLE / "manifest.json", manifest)


def verify_bundle():
    manifest = read_json(BUNDLE / "manifest.json")
    if manifest["engine_inputs"] != input_hash():
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
    inspector = Path(os.environ["CAIRN_COMPILER"]) / "bin/llvm-readobj.exe"
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
            # Hosted Windows Actions runs as administrator. Fail if the rule cannot be installed.
            rule = "Cairn-M0-offline-" + label
            script = ROOT / "tools/ci/offline_test.ps1"
            output = run(["powershell.exe", "-NoProfile", "-File", script,
                          "-Executable", executable, "-RuleName", rule], label, cwd=cwd, env=env, timeout=90)
        else:
            output = run(args, label, cwd=cwd, env=env, timeout=60)
        records = [line.split("CAIRN_SELF_TEST=", 1)[1] for line in output.splitlines() if "CAIRN_SELF_TEST=" in line]
        if len(records) != 1 or "SCRIPT ERROR:" in output or "ERROR:" in output:
            raise RuntimeError(f"{label}: missing self-test report or engine error; see log")
        report = json.loads(records[0])
        if not report.get("passed") or report.get("identity", {}).get("engine_inputs") != input_hash():
            raise RuntimeError(f"{label}: self-test identity or result failed")
        if report.get("game_commit") != os.environ["GITHUB_SHA"]:
            raise RuntimeError("Game pack belongs to another commit")
        write_json(REPORTS / (label + ".json"), report)


def package():
    manifest = verify_bundle()
    game = ROOT / "game"
    templates = ROOT / "build/templates"
    templates.mkdir(exist_ok=True)
    for kind in ["debug", "release"]:
        shutil.copy2(BUNDLE / ("template_" + kind + ".exe"), templates / ("windows_" + kind + ".exe"))
    info = {key: manifest[key] for key in ["engine_inputs", "godot_commit", "voxel_commit"]}
    info.update({"game_commit": os.environ["GITHUB_SHA"], "milestone": "M0",
                 "ci_run": f'https://github.com/{os.environ["GITHUB_REPOSITORY"]}/actions/runs/{os.environ["GITHUB_RUN_ID"]}',
                 "target_performance": "not_run", "renderer": "gl_compatibility",
                 "engine_binaries": {key: value for key, value in manifest["files"].items() if key.endswith(".exe")}})
    write_json(game / "build_info.json", info)
    editor = BUNDLE / "editor.exe"
    output = run([editor, "--headless", "--path", game, "--import"], "editor-import", timeout=300)
    if "SCRIPT ERROR:" in output or "ERROR:" in output:
        raise RuntimeError("Project import reported errors")
    # Run the title/self-test through the matching editor, then both actual export templates.
    self_test(editor, "editor-self-test", game)
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
    write_json(player / "BUILD_INFO.json", info)
    shutil.copytree(BUNDLE / "LICENSES", player / "LICENSES", dirs_exist_ok=True)
    shutil.copy2(ROOT / "distribution/README.txt", player / "README.txt")
    shutil.copy2(ROOT / "distribution/NOTICE.txt", player / "LICENSES/CAIRN-NOTICE.txt")
    if (player / "Cairn.pck").read_bytes()[:4] != b"GDPC":
        raise RuntimeError("Missing or invalid Godot PCK")
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
               "cold_cache": os.environ.get("CAIRN_CACHE_HIT") != "true"})
    shutil.make_archive(str(dist / "Cairn-symbols"), "zip", BUNDLE / "symbols")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["key", "setup", "build", "verify", "package"])
    args = parser.parse_args()
    if args.command == "key":
        value = "windows-m0-" + input_hash()
        print(value)
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write("key=" + value + "\n")
    else:
        {"setup": setup, "build": build, "verify": verify_bundle, "package": package}[args.command]()


if __name__ == "__main__":
    main()
