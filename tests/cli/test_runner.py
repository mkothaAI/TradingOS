import os
import json
from backend.cli import runner


def test_runner_happy_path(capsys):
    rc = runner.main([])
    captured = capsys.readouterr()
    assert rc == 0
    assert "run_id" in captured.out
    assert "status" in captured.out


def test_runner_invalid_input(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not: valid json }")
    rc = runner.main(["--input", str(bad)])
    assert rc != 0
