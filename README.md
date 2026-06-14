# xspatula-lite

A lightweight, notebook-free, metadata-driven workflow engine inspired by Xspatula.

## Clean project layout

```text
example_project/
├─ schemes/
│  └─ local.json
├─ jobs/
│  ├─ setup_db.json
│  └─ setup_processes.json
├─ pilots/
│  ├─ setup_db.txt
│  └─ setup_processes.txt
└─ processes/
   ├─ setup_db/
   │  ├─ 001_create_schemas.json
   │  ├─ 002_create_tables.json
   │  └─ 003_seed_records.json
   └─ setup_processes/
      └─ 001_register_processes.json
```

## Usage

```python
from xspatula_lite import Xspatula

xp = Xspatula(mock=True)
xp.load_scheme("example_project/schemes/local.json")
xp.run_job("setup_db")
xp.run_job("setup_processes")
```

`mock=True` prints/stores execution flow without connecting to a real database.
