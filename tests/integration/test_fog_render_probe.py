"""Prevent optional render evidence from hiding code defects or claiming pixels."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("fog_render_probe", ROOT / "tools/qa/fog_render_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class FogRenderEvidenceTests(unittest.TestCase):
    def test_driver_unavailability_is_explicit(self):
        for code, timed_out in [(1, False), (None, True)]:
            result = probe.classify("ERROR: Unable to initialize OpenGL video driver", code, timed_out)
            self.assertEqual(result["status"], "unavailable")
            self.assertFalse(result["qualified"])

    def test_driver_error_cannot_hide_script_or_shader_defect(self):
        for defect in ["SCRIPT ERROR: Parse Error", "SHADER ERROR: expected expression", "Shader compilation failed"]:
            with self.assertRaises(RuntimeError):
                probe.classify("Unable to initialize OpenGL video driver\n" + defect, 1)

    def test_unknown_crash_or_timeout_is_a_failure(self):
        for code, timed_out in [(0, False), (1, False), (None, True)]:
            with self.assertRaises(RuntimeError):
                probe.classify("Godot startup", code, timed_out)

    def test_supported_readback_retains_independent_bits_and_scope(self):
        bits = [0x0000, 0x3800, 0x3bff, 0x3bff, 0x3bff, 0x3bff, 0x3c00]
        report = {"status": "passed", "passed": True, "qualified": False,
                  "samples": [{"expected_bits": value, "observed_bits": value} for value in bits]}
        self.assertEqual(probe.classify(probe.MARKER + json.dumps(report), 0), report)
        report["samples"][3]["observed_bits"] = 0x3c00
        with self.assertRaises(RuntimeError):
            probe.classify(probe.MARKER + json.dumps(report), 0)

    def test_incomplete_or_failed_marker_is_a_failure(self):
        for report in [{"status": "failed", "passed": False, "qualified": False},
                       {"status": "passed", "passed": True, "qualified": False, "samples": []}]:
            with self.assertRaises(RuntimeError):
                probe.classify(probe.MARKER + json.dumps(report), 0)

    def test_headless_marker_remains_unavailable(self):
        report = {"status": "unavailable", "qualified": False, "context": {"display": "headless"}}
        self.assertEqual(probe.classify(probe.MARKER + json.dumps(report), 0)["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
