from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from c_drive_cleaner import (  # noqa: E402
    CleanTarget,
    clean_file_target,
    human_size,
    scan_file_target,
    select_targets,
    target_label,
    tr,
    validate_target_root,
)


class CleanerCoreTests(unittest.TestCase):
    def test_scan_and_clean_only_old_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            old_file = root / "old.tmp"
            new_file = root / "new.tmp"
            old_file.write_bytes(b"old-data")
            new_file.write_bytes(b"new-data")

            old_timestamp = time.time() - 3 * 24 * 60 * 60
            os.utime(old_file, (old_timestamp, old_timestamp))

            target = CleanTarget(
                key="test",
                label="Test",
                description="Test directory",
                roots=(root,),
                min_age_days=1,
            )

            scan = scan_file_target(target)
            self.assertEqual(scan.file_count, 1)
            self.assertEqual(scan.bytes_total, len(b"old-data"))

            result = clean_file_target(target)
            self.assertEqual(result.files_deleted, 1)
            self.assertEqual(result.bytes_deleted, len(b"old-data"))
            self.assertFalse(old_file.exists())
            self.assertTrue(new_file.exists())

    def test_patterns_limit_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            keep = root / "keep.log"
            delete = root / "delete.tmp"
            keep.write_text("keep", encoding="utf-8")
            delete.write_text("delete", encoding="utf-8")
            old_timestamp = time.time() - 2 * 24 * 60 * 60
            os.utime(keep, (old_timestamp, old_timestamp))
            os.utime(delete, (old_timestamp, old_timestamp))

            target = CleanTarget(
                key="test",
                label="Test",
                description="Test directory",
                roots=(root,),
                min_age_days=1,
                patterns=("*.tmp",),
            )

            scan = scan_file_target(target)
            self.assertEqual(scan.file_count, 1)
            self.assertEqual(scan.bytes_total, len("delete"))

    def test_direct_file_root_can_be_cleaned(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dump = root / "MEMORY.DMP"
            dump.write_bytes(b"dump")

            target = CleanTarget(
                key="dump",
                label="Dump",
                description="Direct file",
                roots=(dump,),
                min_age_days=0,
                patterns=("*.dmp",),
            )

            scan = scan_file_target(target)
            self.assertEqual(scan.file_count, 1)
            self.assertEqual(scan.bytes_total, len(b"dump"))

            result = clean_file_target(target)
            self.assertEqual(result.files_deleted, 1)
            self.assertFalse(dump.exists())

    def test_nonrecursive_target_does_not_scan_children(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            child = root / "child"
            child.mkdir()
            top = root / "top.tmp"
            nested = child / "nested.tmp"
            top.write_text("top", encoding="utf-8")
            nested.write_text("nested", encoding="utf-8")

            target = CleanTarget(
                key="flat",
                label="Flat",
                description="Flat scan",
                roots=(root,),
                min_age_days=0,
                patterns=("*.tmp",),
                recursive=False,
            )

            scan = scan_file_target(target)
            self.assertEqual(scan.file_count, 1)
            self.assertEqual(scan.bytes_total, len("top"))

    def test_deep_selection_includes_deep_but_not_system_targets(self) -> None:
        targets = [
            CleanTarget("a", "A", "Default", default_enabled=True),
            CleanTarget("b", "B", "Deep", default_enabled=False, deep_enabled=True),
            CleanTarget("c", "C", "System", default_enabled=False, deep_enabled=False),
        ]

        self.assertEqual([target.key for target in select_targets(targets, None)], ["a"])
        self.assertEqual([target.key for target in select_targets(targets, None, include_deep=True)], ["a", "b"])
        self.assertEqual(
            [target.key for target in select_targets(targets, None, include_all=True)],
            ["a", "b", "c"],
        )

    def test_rejects_drive_root(self) -> None:
        drive = Path(Path.cwd().anchor)
        with self.assertRaises(ValueError):
            validate_target_root(drive)

    def test_human_size(self) -> None:
        self.assertEqual(human_size(0), "0 B")
        self.assertEqual(human_size(1024), "1.0 KB")

    def test_language_helpers(self) -> None:
        target = CleanTarget("user_temp", "User temp files", "Temp")
        self.assertEqual(target_label(target, "en"), "User temp files")
        self.assertEqual(target_label(target, "zh"), "用户临时文件")
        self.assertEqual(tr("gui.scan", "en"), "Scan")
        self.assertEqual(tr("gui.scan", "zh"), "扫描")


if __name__ == "__main__":
    unittest.main()
