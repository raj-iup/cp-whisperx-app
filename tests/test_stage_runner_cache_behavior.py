import os
import sys
import tempfile
import time
import json

# Ensure repo root on sys.path so pipeline.runner can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.runner import StageRunner, read_manifest


def test_stage_runner_runs_then_skips(tmp_path):
    # Simulate input file
    inp = tmp_path / "input.txt"
    inp.write_text("input-data")
    input_path = str(inp)

    # Stage output dir
    out_dir = tmp_path / "stage_out"
    out_dir_path = str(out_dir)

    # Simple executor that writes an output file and returns outputs list
    def executor(stage_name, inputs, params, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, "result.txt")
        with open(out_path, "w") as fh:
            fh.write("computed")
        return [out_path]

    # Create StageRunner and run
    sr = StageRunner(stage_name="unit_test_stage", output_dir=out_dir_path, inputs=[input_path], params={}, force=False)
    ran_first = sr.run(executor)
    assert ran_first is True

    manifest1 = read_manifest(out_dir_path)
    assert manifest1 and "timestamp" in manifest1
    ts1 = manifest1["timestamp"]

    # Wait to ensure time delta if the runner may update last_checked_ts
    time.sleep(1)

    # Second invocation should be skipped
    ran_second = sr.run(executor)
    assert ran_second is False

    manifest2 = read_manifest(out_dir_path)
    # The 'timestamp' (manifest's creation time) should remain unchanged after a SKIP
    assert manifest2["timestamp"] == ts1
    assert "last_checked_ts" in manifest2 and manifest2["last_checked_ts"] >= ts1
