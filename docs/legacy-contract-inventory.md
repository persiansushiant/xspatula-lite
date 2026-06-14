# Legacy Xspatula Contract Inventory

This document records contracts confirmed from the legacy Xspatula repository.

## Confirmed setup process IDs

- `create_schema`
- `create_table`
- `table_insert`
- `delete_database`
- `delete_schema`
- `delete_table`

`table_update` and `grant` are not part of the confirmed shipped JSON contracts.

## Scheme contract

Legacy scheme files use:

```json
{
  "project_path": "./xspatula",
  "postgresdb": {
    "host": "...",
    "port": 5432,
    "db": "...",
    "user_name": "...",
    "password": "...",
    "db_users": [
      {
        "user_id": "...",
        "password": "...",
        "role": "..."
      }
    ]
  },
  "process": [
    {
      "execute": true,
      "verbose": 1,
      "overwrite": false,
      "delete": false,
      "src_path": {
        "volume": ".",
        "ext": "json"
      }
    }
  ]
}
```

`xspatula-lite` also supports the cleaner consumer-project layout:

```json
{
  "project_path": "..",
  "database": {"type": "mock"},
  "paths": {
    "jobs": "jobs",
    "pilots": "pilots",
    "processes": "processes"
  },
  "defaults": {
    "execute": true,
    "verbose": 1,
    "overwrite": false,
    "delete": false
  }
}
```

## Job contract

Legacy format:

```json
{
  "process": {
    "job_folder": "setup_db",
    "process_sub_folder": "json_core",
    "pilot_file": "db_xspatula_core_setup.txt"
  }
}
```

Clean format:

```json
{
  "job_id": "setup_db",
  "pilot": "setup_db.txt",
  "process_folder": "setup_db"
}
```

## Pilot contract

- Plain text.
- One process JSON filename per non-empty line.
- Lines starting with `#` are comments.
- Empty lines are ignored.
- Execution order is top-to-bottom.

## Process JSON contracts

### create_schema

```json
{
  "process": [
    {
      "process_id": "create_schema",
      "overwrite": false,
      "delete": false,
      "parameters": {
        "schema": "community"
      }
    }
  ]
}
```

### create_table

```json
{
  "process": [
    {
      "process_id": "create_table",
      "overwrite": false,
      "delete": false,
      "parameters": {
        "schema": "soil",
        "table": "samples",
        "command": [
          "sample_id INTEGER",
          "sample_name TEXT",
          "ph REAL",
          "PRIMARY KEY(sample_id)"
        ]
      }
    }
  ]
}
```

### table_insert

```json
{
  "process": [
    {
      "process_id": "table_insert",
      "parameters": {
        "schema": "soil",
        "table": "samples",
        "command": {
          "columns": ["sample_id", "sample_name", "ph"],
          "values": [
            [1, "sample_a", 6.8]
          ]
        }
      }
    }
  ]
}
```

## Metadata registry entities

Framework-level registry entities:

- `root_process`
- `process`
- `process_parameter`
- `process_parameter_set_value`
- `process_parameter_minmax`
- `process_parameter_schema_table`
- `process_parameter_permission`
- `process_parameter_default`

### root_process

Fields:

- `id`
- `root_process`
- `title`
- `label`
- `creator_id`
- `create_timestamp`

### process

Fields:

- `id`
- `root_process_id`
- `root_process`
- `process`
- `min_user_stratum`
- `title`
- `label`
- `creator_id`
- `create_timestamp`
- `last_update_timestamp`

### process_parameter

Fields:

- `id`
- `process_id`
- `parent`
- `element`
- `parameter`
- `parameter_type`
- `required`
- `default_value`
- `hint`

### process_parameter_set_value

Fields:

- `id`
- `process_id`
- `parent`
- `element`
- `parameter`
- `value`
- `label`

### process_parameter_minmax

Fields:

- `id`
- `process_id`
- `parent`
- `element`
- `parameter`
- `minval`
- `maxval`

### process_parameter_schema_table

Fields:

- `id`
- `process_id`
- `parameter_id`
- `in_schema`
- `in_table`
- `write`

### process_parameter_permission

Fields:

- `id`
- `process_id`
- `parameter_id`
- `column_update`
- `column_delete`

### process_parameter_default

Fields:

- `id`
- `process_id`
- `parameter_id`
- `src_schema`
- `src_table`
- `src_column`
- `search_column`
- `search_object`
