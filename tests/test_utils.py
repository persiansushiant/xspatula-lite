from xspatula_lite.utils import require_keys


def test_require_keys():
    data = {
        "a": 1,
        "b": 2,
    }

    require_keys(
        data,
        ["a", "b"],
        context="test data",
    )