import json
from pathlib import Path
from backend.schemas.json_schemas import generate_all


def test_json_schema_generation_runs(tmp_path):
    # run generator and ensure files created
    paths = generate_all()
    assert len(paths) >= 1
