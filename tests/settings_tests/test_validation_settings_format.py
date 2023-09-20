import os
from pathlib import Path

import pytest

from hyperpack import HyperPack, SettingsError

LIB_PATH = os.getcwd()


@pytest.mark.parametrize(
    "settings,error_msg",
    [
        (1, SettingsError.TYPE),
        (1.2, SettingsError.TYPE),
        ("[]", SettingsError.TYPE),
    ],
)
def test_settings_format_validation(settings, error_msg, request):
    test_data = request.getfixturevalue("test_data")
    caplog = request.getfixturevalue("caplog")
    with pytest.raises(SettingsError) as exc_info:
        prob = HyperPack(**test_data, settings=settings)
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    # now tests for changing the _settings value
    proper_settings = {}
    prob = HyperPack(**test_data, settings=proper_settings)
    caplog = request.getfixturevalue("caplog")
    with pytest.raises(SettingsError) as exc_info:
        prob.settings = settings
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


def test_settings_deletion_raises_error(caplog, test_data):
    prob = HyperPack(**test_data)
    with pytest.raises(SettingsError) as exc_info:
        del prob.settings
    assert str(exc_info.value) == SettingsError.CANT_DELETE_SETTINGS
    assert SettingsError.CANT_DELETE_SETTINGS in caplog.text
