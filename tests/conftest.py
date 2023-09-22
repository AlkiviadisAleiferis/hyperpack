import os
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

LIB_PATH = Path(os.getcwd())


@pytest.fixture
def test_data():
    return {
        "items": {"test_id": {"w": 10, "l": 10}},
        "containers": {"cont_id": {"W": 100, "L": 100}},
    }


@pytest.fixture
def HyperSearchProcess_mock(mocker):
    process_mock = mocker.patch("hyperpack.heuristics.HyperSearchProcess")
    return process_mock


@pytest.fixture
def cpu_count_mock(mocker):
    mocker.patch("hyperpack.heuristics.cpu_count", return_value=2)
    return cpu_count_mock


@pytest.fixture
def platform_os_mock(mocker):
    mocker.patch("hyperpack.heuristics.platform.system", return_value="Windows")
    return cpu_count_mock


@pytest.fixture
def point_gen_settings():
    return {
        "rotation": False,
    }


@pytest.fixture
def plotly_lib_mock_version(mocker):
    plotly_mock = MagicMock(__version__="5.13.0")
    modules = {"plotly": plotly_mock}
    import_mock = mocker.patch("hyperpack.heuristics.sys.modules", modules)
    return import_mock


@pytest.fixture
def plotly_lib_mock_not_found(mocker):
    modules = {"plotly": None}
    import_mock = mocker.patch("hyperpack.heuristics.sys.modules", modules)
    return import_mock


@pytest.fixture
def kaleido_lib_mock_version(mocker):
    kaleido_mock = MagicMock()
    kaleido_mock.__version__ = "0.2.0"
    modules = {"kaleido": kaleido_mock}
    import_mock = mocker.patch("hyperpack.heuristics.sys.modules", modules)
    return import_mock


@pytest.fixture
def kaleido_lib_mock_not_found(mocker):
    modules = {"kaleido": None}
    import_mock = mocker.patch("hyperpack.heuristics.sys.modules", modules)
    return import_mock
