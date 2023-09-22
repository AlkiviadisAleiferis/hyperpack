import os

import pytest

from hyperpack import HyperPack, SettingsError

LIB_PATH = os.getcwd()


def test_settings_figure_plotly_version(plotly_lib_mock_version, caplog, test_data):
    error_msg = SettingsError.PLOTLY_VERSION
    settings = {"figure": {"export": {"type": "html"}}}
    with pytest.raises(SettingsError) as exc_info:
        prob = HyperPack(**test_data, settings=settings)
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    # now if "figure" wasn't provided for plotly check
    settings = {}
    prob = HyperPack(**test_data, settings=settings)
    prob.solve()
    with pytest.raises(SettingsError) as exc_info:
        prob.create_figure()
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


def test_settings_figure_plotly_not_found(plotly_lib_mock_not_found, caplog, test_data):
    error_msg = SettingsError.PLOTLY_NOT_INSTALLED
    settings = {"figure": {"export": {"type": "html"}}}
    with pytest.raises(SettingsError) as exc_info:
        prob = HyperPack(**test_data, settings=settings)
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    # now if "figure" wasn't provided for plotly check
    settings = {}
    prob = HyperPack(**test_data, settings=settings)
    prob.solve()
    with pytest.raises(SettingsError) as exc_info:
        prob.create_figure()
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


def test_settings_figure_kaleido_not_found(kaleido_lib_mock_not_found, caplog, test_data):
    error_msg = SettingsError.FIGURE_EXPORT_KALEIDO_MISSING
    settings = {
        "figure": {
            "export": {
                "type": "image",
                "path": LIB_PATH,
                "format": "png",
                "file_name": "okay_name",
            }
        }
    }
    with pytest.raises(SettingsError) as exc_info:
        prob = HyperPack(**test_data, settings=settings)
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


def test_settings_figure_plotly_version(kaleido_lib_mock_version, caplog, test_data):
    error_msg = SettingsError.FIGURE_EXPORT_KALEIDO_VERSION
    settings = {"figure": {"export": {"type": "image", "path": os.getcwd(), "format": "png"}}}
    with pytest.raises(SettingsError) as exc_info:
        prob = HyperPack(**test_data, settings=settings)
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text
