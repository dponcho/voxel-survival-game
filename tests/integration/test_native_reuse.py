"""Cache invalidation, corruption and artifact trust regressions (cloud only)."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.parse
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/ci"))
import pipeline
import native_bundle


class NativeReuseTests(unittest.TestCase):
    def test_only_native_inputs_invalidate_binaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ["native", "build/config", "build/patches", "tools/ci"]:
                shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copy2(ROOT / "build/dependencies.lock.json", root / "build/dependencies.lock.json")
            original = pipeline.input_hash(root)
            for name in ["game/scripts/player.gd", "game/assets/texture.png", "game/project.godot",
                         "game/export_presets.cfg", "tools/ci/pipeline.py", "tools/ci/native_bundle.py",
                         "tools/qa/test.py", ".github/workflows/windows-build.yml", "README.md",
                         "build/config/windows-system-dlls.json"]:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("ordinary export input changed")
                self.assertEqual(original, pipeline.input_hash(root), name)
            for name in ["native/sandbox_world/godot/fixture_generator.cpp", "build/config/windows.json",
                         "build/patches/voxel/m1-admission.json", "build/dependencies.lock.json",
                         "tools/ci/engine_recipe.py", "tools/ci/build_support.py"]:
                path = root / name
                before = path.read_bytes()
                path.write_bytes(before + b"changed")
                self.assertNotEqual(original, pipeline.input_hash(root), name)
                path.write_bytes(before)

    def test_artifact_scope_does_not_promote_pr_binaries_to_main(self):
        run = {"head_repository": {"full_name": "owner/game"}, "event": "push", "head_branch": "main"}
        self.assertTrue(native_bundle.trusted_run(run, "owner/game", "main", None))
        self.assertTrue(native_bundle.trusted_run(run, "owner/game", "main", 2))
        run.update(event="pull_request", head_branch="feature", pull_requests=[{"number": 2}])
        self.assertTrue(native_bundle.trusted_run(run, "owner/game", "main", 2))
        self.assertFalse(native_bundle.trusted_run(run, "owner/game", "main", None))
        self.assertFalse(native_bundle.trusted_run(run, "owner/game", "main", 3))
        run["head_repository"] = {"full_name": "fork/game"}
        self.assertFalse(native_bundle.trusted_run(run, "owner/game", "main", 2))

    def test_bundle_identity_and_payload_are_both_verified(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory)
            executable = bundle / "editor.exe"
            executable.write_bytes(b"test binary")
            manifest = {"engine_inputs": "correct", "files": {"editor.exe": pipeline.digest(executable)}}
            (bundle / "manifest.json").write_text(json.dumps(manifest))
            with patch.object(pipeline, "BUNDLE", bundle), patch.object(pipeline, "input_hash", return_value="correct"), patch.object(pipeline, "legacy_identity", return_value=None):
                pipeline.verify_bundle()
                executable.write_bytes(b"tampered")
                with self.assertRaisesRegex(RuntimeError, "Corrupt"):
                    pipeline.verify_bundle()
                manifest["engine_inputs"] = "other native source"
                (bundle / "manifest.json").write_text(json.dumps(manifest))
                with self.assertRaisesRegex(RuntimeError, "Stale"):
                    pipeline.verify_bundle()

    def test_legacy_migration_is_exact_not_a_restore_prefix(self):
        migration = json.loads((ROOT / "build/native-cache-migration.json").read_text())
        with patch.object(pipeline, "input_hash", return_value=migration["native_key"]):
            self.assertEqual(pipeline.legacy_identity(), migration["legacy_engine_inputs"])
        with patch.object(pipeline, "input_hash", return_value="changed-native-key"):
            self.assertIsNone(pipeline.legacy_identity())

    def test_native_artifact_lookup_paginates_exact_name_results(self):
        name = "Cairn-native-windows-native-v2-key"
        pages = []
        first = [{"id": index, "name": name if index == 0 else "unrelated"}
                 for index in range(100)]
        second = [{"id": 101, "name": name}]

        def fake_api(path):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
            self.assertEqual(query["name"], [name])
            self.assertEqual(query["per_page"], ["100"])
            page = int(query["page"][0])
            pages.append(page)
            return {"artifacts": first if page == 1 else second}

        with patch.object(native_bundle, "api", side_effect=fake_api):
            found = native_bundle.named_artifacts(name)
        self.assertEqual(pages, [1, 2])
        self.assertEqual([item["id"] for item in found], [0, 101])

    def test_artifact_reuse_requires_more_than_seven_days_remaining(self):
        now = datetime(2026, 9, 25, tzinfo=timezone.utc)
        expired_soon = (now + timedelta(days=7), {"id": 10}, 100)
        reusable = (now + timedelta(days=8), {"id": 11}, 101)
        missing_expiry = (None, {"id": 12}, 102)
        self.assertEqual(native_bundle.reusable_artifact(
            [expired_soon, reusable, missing_expiry], now=now), reusable)
        self.assertIsNone(native_bundle.reusable_artifact(
            [expired_soon, missing_expiry], now=now))

    def test_restore_emits_reusable_artifact_outputs_only_with_retention(self):
        event = {"repository": {"default_branch": "main"}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            bundle.mkdir()
            (bundle / "manifest.json").write_text("{}")
            output = root / "github-output"
            output.touch()
            now = datetime.now(timezone.utc)
            long_lived = (now + timedelta(days=8), {"id": 321}, 654)
            env = {"GITHUB_EVENT_PATH": str(root / "event.json"),
                   "GITHUB_REPOSITORY": "owner/game", "GITHUB_OUTPUT": str(output)}
            with patch.dict("os.environ", env), \
                 patch.object(pipeline, "read_json", return_value=event), \
                 patch.object(pipeline, "input_hash", return_value="key"), \
                 patch.object(pipeline, "BUNDLE", bundle), \
                 patch.object(pipeline, "verify_bundle", return_value={}), \
                 patch.object(pipeline, "write_json"), \
                 patch.object(native_bundle, "trusted_qualified_artifacts", return_value=[long_lived]), \
                 patch.object(native_bundle, "download_artifact", side_effect=AssertionError("cache hit downloads no artifact")):
                native_bundle.restore()
            values = dict(line.split("=", 1) for line in output.read_text().splitlines())
            self.assertEqual(values, {"source": "cache", "artifact_id": "321", "artifact_run_id": "654"})

            output.write_text("")
            short_lived = (datetime.now(timezone.utc) + timedelta(days=7), {"id": 322}, 655)
            with patch.dict("os.environ", env), \
                 patch.object(pipeline, "read_json", return_value=event), \
                 patch.object(pipeline, "input_hash", return_value="key"), \
                 patch.object(pipeline, "BUNDLE", bundle), \
                 patch.object(pipeline, "verify_bundle", return_value={}), \
                 patch.object(pipeline, "write_json"), \
                 patch.object(native_bundle, "trusted_qualified_artifacts", return_value=[short_lived]), \
                 patch.object(native_bundle, "download_artifact", side_effect=AssertionError("cache hit downloads no artifact")):
                native_bundle.restore()
            values = dict(line.split("=", 1) for line in output.read_text().splitlines())
            self.assertEqual(values, {"source": "cache", "artifact_id": "", "artifact_run_id": ""})

    def test_artifact_candidates_require_trusted_qualified_run(self):
        artifact = {"id": 3, "name": "exact", "expired": False,
                    "digest": "sha256:abc", "expires_at": "2026-10-25T00:00:00Z",
                    "workflow_run": {"id": 45}}
        run = {"head_repository": {"full_name": "owner/game"},
               "event": "push", "head_branch": "main"}
        with patch.object(native_bundle, "named_artifacts", return_value=[artifact]), \
             patch.object(native_bundle, "api", side_effect=[run, {"jobs": [
                 {"name": "native-binaries", "conclusion": "success"}]}]):
            found = native_bundle.trusted_qualified_artifacts(
                "exact", "owner/game", "main", None)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0][1]["id"], 3)
        self.assertEqual(found[0][2], 45)

        unqualified = {"jobs": [{"name": "native-binaries", "conclusion": "failure"}]}
        with patch.object(native_bundle, "named_artifacts", return_value=[artifact]), \
             patch.object(native_bundle, "api", side_effect=[run, unqualified]):
            self.assertEqual(native_bundle.trusted_qualified_artifacts(
                "exact", "owner/game", "main", None), [])


if __name__ == "__main__":
    unittest.main()
