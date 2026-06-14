from xspatula_lite.dispatcher import Dispatcher
from xspatula_lite.models import ProcessStep
from xspatula_lite.registry import ProcessRegistry


def dispatch_step(process_id, parameters):
    registry = ProcessRegistry()
    dispatcher = Dispatcher(registry=registry, verbose=0)
    step = ProcessStep(
        source_file=None,
        index=1,
        process_id=process_id,
        parameters=parameters,
        options={"execute": True},
        raw={"process_id": process_id, "parameters": parameters},
    )
    dispatcher.dispatch(step)
    return registry


def test_register_root_process():
    registry = dispatch_step(
        "add_root_process",
        {"root_process": "ai4soil", "title": "AI4Soil", "label": "AI4Soil workflows"},
    )
    assert "ai4soil" in registry.root_processes
    assert registry.root_processes["ai4soil"]["title"] == "AI4Soil"


def test_register_process_with_min_user_stratum():
    registry = dispatch_step(
        "add_process",
        {
            "root_process": "ai4soil",
            "process": "import_data",
            "min_user_stratum": 0,
            "title": "Import soil data",
        },
    )
    assert registry.processes["import_data"]["min_user_stratum"] == 0


def test_register_all_confirmed_parameter_metadata_entities():
    entities = [
        ("process_parameter", "process_parameter"),
        ("process_parameter_set_value", "process_parameter_set_value"),
        ("process_parameter_minmax", "process_parameter_minmax"),
        ("process_parameter_schema_table", "process_parameter_schema_table"),
        ("process_parameter_permission", "process_parameter_permission"),
        ("process_parameter_default", "process_parameter_default"),
    ]

    registry = ProcessRegistry()
    dispatcher = Dispatcher(registry=registry, verbose=0)

    for process_id, collection_key in entities:
        step = ProcessStep(
            source_file=None,
            index=1,
            process_id=process_id,
            parameters={"process": "import_data", "parameter": "sample_id"},
            options={"execute": True},
            raw={},
        )
        dispatcher.dispatch(step)

    snapshot = registry.snapshot()
    for _, collection_key in entities:
        assert "import_data" in snapshot[collection_key]
        assert snapshot[collection_key]["import_data"][0]["parameter"] == "sample_id"
