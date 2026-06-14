import json
from pathlib import Path

from xspatula_lite import Xspatula


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def build_project(tmp_path: Path) -> Path:
    write_json(
        tmp_path / "schemes" / "local.json",
        {
            "project_path": "..",
            "database": {"type": "mock"},
            "paths": {"jobs": "jobs", "pilots": "pilots", "processes": "processes"},
            "defaults": {"execute": True, "verbose": 0, "overwrite": False, "delete": False},
        },
    )
    write_json(
        tmp_path / "jobs" / "setup_db.json",
        {"job_id": "setup_db", "pilot": "setup_db.txt", "process_folder": "setup_db"},
    )
    (tmp_path / "pilots").mkdir(exist_ok=True)
    (tmp_path / "pilots" / "setup_db.txt").write_text(
        "001_create_schema.json\n002_create_table.json\n003_insert.json\n", encoding="utf-8"
    )
    write_json(
        tmp_path / "processes" / "setup_db" / "001_create_schema.json",
        {"process": [{"process_id": "create_schema", "parameters": {"schema": "soil"}}]},
    )
    write_json(
        tmp_path / "processes" / "setup_db" / "002_create_table.json",
        {
            "process": [
                {
                    "process_id": "create_table",
                    "parameters": {
                        "schema": "soil",
                        "table": "samples",
                        "command": ["sample_id INTEGER", "sample_name TEXT"],
                    },
                }
            ]
        },
    )
    write_json(
        tmp_path / "processes" / "setup_db" / "003_insert.json",
        {
            "process": [
                {
                    "process_id": "table_insert",
                    "parameters": {
                        "schema": "soil",
                        "table": "samples",
                        "command": {"columns": ["sample_id", "sample_name"], "values": [[1, "alpha"]]},
                    },
                }
            ]
        },
    )
    return tmp_path / "schemes" / "local.json"


def test_mock_setup_db_workflow(tmp_path):
    scheme = build_project(tmp_path)
    xp = Xspatula(mock=True, verbose=0)
    xp.load_scheme(scheme)
    xp.run_job("setup_db")

    assert any("CREATE SCHEMA" in sql for sql in xp.db.executed)
    assert any("CREATE TABLE" in sql for sql in xp.db.executed)
    assert any("INSERT INTO" in sql for sql in xp.db.executed)


def test_mock_process_registration():
    xp = Xspatula(mock=True, verbose=0)
    step = xp.process_file_loader.from_process(
        "add_root_process",
        {"root_process": "manage_apparatus", "title": "Manage apparatus"},
    )
    xp.dispatcher.dispatch(step, defaults={"execute": True})

    step = xp.process_file_loader.from_process(
        "add_process",
        {"root_process": "manage_apparatus", "process": "add_apparatus", "min_user_stratum": 0},
    )
    xp.dispatcher.dispatch(step, defaults={"execute": True})

    assert "manage_apparatus" in xp.registry.root_processes
    assert "add_apparatus" in xp.registry.processes
    assert xp.registry.processes["add_apparatus"]["min_user_stratum"] == 0
