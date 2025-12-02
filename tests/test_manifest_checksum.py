import os
import sys
import shutil
import tempfile

# Ensure repo root on sys.path so pipeline.runner can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.runner import compute_inputs_checksum


def test_compute_inputs_checksum_detects_file_changes(tmp_path):
    # Create a small directory with files
    d = tmp_path / "data"
    d.mkdir()
    f1 = d / "a.txt"
    f1.write_text("hello")
    sub = d / "sub"
    sub.mkdir()
    f2 = sub / "b.txt"
    f2.write_text("world")

    # Compute initial checksum
    checksum1 = compute_inputs_checksum([str(d)])

    # Modify a nested file and expect checksum to change
    f2.write_text("WORLD")
    checksum2 = compute_inputs_checksum([str(d)])
    assert checksum1 != checksum2

    # Recompute to ensure deterministic output
    checksum3 = compute_inputs_checksum([str(d)])
    assert checksum2 == checksum3
