"""Native compilation recipe. Only this recipe, native sources, pins and flags key binaries."""
import os
from pathlib import Path
import shutil
import sys
from build_support import (ROOT, LOCK, BUNDLE, REPORTS, read_json, write_json, digest,
                      download, extract, run, stage_source, copy_licenses)


from pipeline import input_hash


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
    for patch_file in sorted((ROOT / "build/patches/voxel").glob("*.json")):
        for change in read_json(patch_file):
            target = (engine / "modules/voxel" / change["path"]).resolve()
            if not target.is_relative_to((engine / "modules/voxel").resolve()):
                raise RuntimeError("Patch path escapes the pinned module")
            source = target.read_text(encoding="utf-8")
            if change["replacement"] in source:
                continue
            if source.count(change["old"]) != 1:
                raise RuntimeError("Pinned source patch does not match: " + change["path"])
            target.write_text(source.replace(change["old"], change["replacement"]), encoding="utf-8", newline="\n")
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


