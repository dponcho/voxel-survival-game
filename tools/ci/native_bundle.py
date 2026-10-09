"""Restore a qualified exact native artifact, or record a genuine cold miss.

No credentials cross the GitHub download redirect. Default-branch builds never
consume PR artifacts; a PR can consume its own previous runs or the default branch.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import urllib.error
import urllib.parse
import urllib.request

import pipeline as p


def trusted_run(run, repository, default_branch, pr_number):
    if (run.get("head_repository") or {}).get("full_name") != repository:
        return False
    if run.get("event") in {"push", "workflow_dispatch"} and run.get("head_branch") == default_branch:
        return True
    return bool(pr_number and run.get("event") == "pull_request" and any(
        item.get("number") == pr_number for item in run.get("pull_requests", [])))


def api(path):
    request = urllib.request.Request("https://api.github.com/repos/" + os.environ["GITHUB_REPOSITORY"] + path,
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                 "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def named_artifacts(name):
    """Return every exact-name artifact, following the Actions API page limit."""
    artifacts = []
    page = 1
    while True:
        query = urllib.parse.urlencode({"name": name, "per_page": 100, "page": page})
        batch = api("/actions/artifacts?" + query).get("artifacts", [])
        artifacts.extend(item for item in batch if item.get("name") == name)
        if len(batch) < 100:
            return artifacts
        page += 1


def expiry(artifact):
    value = artifact.get("expires_at")
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (AttributeError, ValueError):
        return None


def trusted_qualified_artifacts(name, repository, default_branch, pr_number):
    """Find matching artifacts whose source run is trusted and passed native qualification."""
    candidates = []
    for artifact in named_artifacts(name):
        if artifact.get("expired") or not (artifact.get("digest") or "").startswith("sha256:"):
            continue
        run_id = artifact.get("workflow_run", {}).get("id")
        if run_id is None:
            continue
        run = api("/actions/runs/" + str(run_id))
        if not trusted_run(run, repository, default_branch, pr_number):
            continue
        jobs = api("/actions/runs/" + str(run_id) + "/jobs?per_page=100").get("jobs", [])
        if not any(job.get("name", "").endswith("native-binaries") and job.get("conclusion") == "success"
                   for job in jobs):
            continue
        candidates.append((expiry(artifact), artifact, run_id))
    # Prefer the artifact with the longest remaining lifetime. Missing or malformed
    # expiries remain usable as restore sources, but never as downstream reuse sources.
    return sorted(candidates, key=lambda item: item[0] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)


def reusable_artifact(candidates, now=None):
    """Return an artifact only when it has more than seven days of retention left."""
    now = now or datetime.now(timezone.utc)
    return next((item for item in candidates
                 if item[0] and item[0] > now + timedelta(days=7)), None)


def write_selection(source, key, artifact_id="", artifact_run_id=""):
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write("source=" + source + "\n")
        output.write("artifact_id=" + str(artifact_id) + "\n")
        output.write("artifact_run_id=" + str(artifact_run_id) + "\n")
    p.write_json(p.REPORTS / "native-selection.json", {
        "source": source, "key": key, "artifact_id": artifact_id,
        "artifact_run_id": artifact_run_id})


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download_artifact(artifact, destination):
    url = "https://api.github.com/repos/" + os.environ["GITHUB_REPOSITORY"] + "/actions/artifacts/" + str(int(artifact["id"])) + "/zip"
    request = urllib.request.Request(url, headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"]})
    try:
        urllib.request.build_opener(NoRedirect).open(request, timeout=60)
        raise RuntimeError("Expected a signed artifact redirect")
    except urllib.error.HTTPError as error:
        if error.code != 302:
            raise
        signed_url = error.headers["Location"]
    if urllib.parse.urlparse(signed_url).scheme != "https":
        raise RuntimeError("Artifact redirect must use HTTPS")
    with urllib.request.urlopen(signed_url, timeout=120) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)
    if artifact.get("digest") != "sha256:" + p.digest(destination):
        raise RuntimeError("Native artifact archive digest mismatch")


def restore():
    event = p.read_json(Path(os.environ["GITHUB_EVENT_PATH"]))
    pr_number = event.get("pull_request", {}).get("number")
    name = "Cairn-native-windows-native-v2-" + p.input_hash()
    candidates = trusted_qualified_artifacts(
        name, os.environ["GITHUB_REPOSITORY"], event["repository"]["default_branch"], pr_number)
    artifact_reuse = reusable_artifact(candidates)

    if (p.BUNDLE / "manifest.json").exists():
        p.verify_bundle()
        source = "cache"
    else:
        source = "built"
        if candidates:
            _, artifact, run_id = candidates[0]
            archive = p.ROOT / "build/restored-native.zip"
            archive.parent.mkdir(exist_ok=True)
            download_artifact(artifact, archive)
            p.extract(archive, p.BUNDLE)
            p.verify_bundle()
            source = "artifact"
            p.write_json(p.REPORTS / "native-restore.json", {
                "artifact_id": artifact["id"], "run_id": run_id, "digest": artifact["digest"]})
    print("Native bundle source: " + source, flush=True)
    reusable_id = artifact_reuse[1].get("id", "") if artifact_reuse else ""
    reusable_run_id = artifact_reuse[2] if artifact_reuse else ""
    write_selection(source, p.input_hash(), reusable_id, reusable_run_id)


def inspector():
    """Ship the pinned audit utility with the build bundle, never with the player."""
    manifest = p.verify_bundle()
    target = p.BUNDLE / "audit-tools"
    if (target / "llvm-readobj.exe").exists():
        return
    lock = p.read_json(p.LOCK)
    compiler = p.ROOT / "build/toolchain" / lock["compiler"]["version"]
    if not compiler.exists():
        p.extract(p.download(lock["compiler"], "compiler.zip"), compiler.parent)
    target.mkdir(exist_ok=True)
    for path in [compiler / "bin/llvm-readobj.exe", *sorted((compiler / "bin").glob("*.dll"))]:
        shutil.copy2(path, target / path.name)
    manifest["files"] = {path.relative_to(p.BUNDLE).as_posix(): p.digest(path)
                         for path in sorted(p.BUNDLE.rglob("*")) if path.is_file() and path.name != "manifest.json"}
    p.write_json(p.BUNDLE / "manifest.json", manifest)
    p.verify_bundle()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["restore", "inspector"])
    args = parser.parse_args()
    {"restore": restore, "inspector": inspector}[args.command]()
