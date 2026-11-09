"""Pinned source acquisition and native command support shared by CI."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
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
            process = subprocess.Popen(args, cwd=cwd, env=env, stdout=output,
                                       stderr=subprocess.STDOUT)
            while True:
                remaining = timeout - (time.monotonic() - started)
                if remaining <= 0:
                    process.kill()
                    process.wait()
                    raise subprocess.TimeoutExpired(args, timeout)
                try:
                    code = process.wait(timeout=min(30, remaining))
                    break
                except subprocess.TimeoutExpired:
                    with log.open("rb") as progress:
                        progress.seek(max(0, log.stat().st_size - 2048))
                        lines = progress.read().decode("utf-8", errors="replace").splitlines()
                    print(f"{label}: {int(time.monotonic() - started)}s; " + (lines[-1] if lines else "running"), flush=True)
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


def copy_licenses(source, destination):
    for path in source.rglob("*"):
        if path.is_file() and any(word in path.name.lower() for word in ["license", "licence", "copyright", "copying", "notice"]):
            target = destination / path.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


