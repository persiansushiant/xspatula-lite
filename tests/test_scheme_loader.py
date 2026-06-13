from pathlib import Path

from xspatula_lite.scheme import SchemeLoader


def test_load_scheme():
    scheme_file = (
        Path(__file__).parent
        / "fixtures"
        / "schemes"
        / "minimal_scheme.json"
    )

    loader = SchemeLoader()
    scheme = loader.load(scheme_file)

    assert scheme is not None
    assert scheme.project_path is not None