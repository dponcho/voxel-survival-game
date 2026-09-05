"""Packaging and build identity regression tests; run in cloud CI."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("pipeline", ROOT / "tools/ci/pipeline.py")
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


class PackagingTests(unittest.TestCase):
    def test_architecture_and_delay_imports_are_audited(self):
        output = "Machine: IMAGE_FILE_MACHINE_AMD64 (0x8664)\nImport {\n Name: KERNEL32.dll\n}\nDelayImport {\n Name: VCRUNTIME140.dll\n}\n"
        self.assertEqual(pipeline.imported_dlls(output), {"kernel32.dll", "vcruntime140.dll"})
        self.assertFalse(pipeline.is_system_dll("vcruntime140.dll"))
        self.assertFalse(pipeline.is_system_dll("libc++.dll"))
        self.assertFalse(pipeline.is_system_dll("api-ms-win-unknown-custom.dll"))
        self.assertTrue(pipeline.is_system_dll("dwrite.dll"))
        self.assertTrue(pipeline.is_system_dll("api-ms-win-core-registry-l1-1-0.dll"))
        self.assertTrue(pipeline.is_system_dll("api-ms-win-crt-runtime-l1-1-0.dll"))
        with self.assertRaises(RuntimeError):
            pipeline.imported_dlls(output.replace("AMD64 (0x8664)", "I386 (0x14C)"))
        with self.assertRaises(RuntimeError):
            pipeline.imported_dlls("garbage")

    def test_zip_paths_cannot_escape(self):
        for name in ["../outside", "..\\outside", "C:/outside"]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                archive = Path(temp) / "bad.zip"
                with zipfile.ZipFile(archive, "w") as zipped:
                    zipped.writestr(name, "bad")
                with self.assertRaises(RuntimeError):
                    pipeline.extract(archive, Path(temp) / "fresh")

    def test_native_and_configuration_changes_invalidate_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "build/config").mkdir(parents=True)
            (root / "native").mkdir()
            (root / "build/dependencies.lock.json").write_text("{}")
            original = pipeline.input_hash(root)
            (root / "native/module.cpp").write_text("new native source")
            native = pipeline.input_hash(root)
            self.assertNotEqual(original, native)
            (root / "build/config/flags.json").write_text("new compiler flags")
            self.assertNotEqual(native, pipeline.input_hash(root))

    def test_space_unicode_extraction_preserves_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "candidate.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("Cairn.pck", b"GDPC\x00\xff")
            destination = Path(temp) / "clean path é 世界"
            pipeline.extract(archive, destination)
            self.assertEqual((destination / "Cairn.pck").read_bytes(), b"GDPC\x00\xff")


if __name__ == "__main__":
    unittest.main()
