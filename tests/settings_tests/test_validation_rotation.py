import pytest

from hyperpack import HyperPack, SettingsError


@pytest.mark.parametrize(
    "settings,error_msg",
    [
        ({"rotation": 0}, SettingsError.ROTATION_TYPE),
        ({"rotation": "str"}, SettingsError.ROTATION_TYPE),
        ({"rotation": [0]}, SettingsError.ROTATION_TYPE),
        (
            {"rotation": {"key": 0}},
            SettingsError.ROTATION_TYPE,
        ),
    ],
)
def test_settings_rotation_validation_error(settings, error_msg, request):
    test_data = request.getfixturevalue("test_data")
    caplog = request.getfixturevalue("caplog")

    with pytest.raises(SettingsError) as exc_info:
        prob = HyperPack(**test_data, settings=settings)
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    # now tests for changing the _settings value
    prob = HyperPack(**test_data)
    caplog = request.getfixturevalue("caplog")
    with pytest.raises(SettingsError) as exc_info:
        prob.settings = settings
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


def test_settings_rotation___ok(test_data):
    settings = {"rotation": False}
    prob = HyperPack(**test_data, settings=settings)
    assert prob._rotation is False
    assert prob.settings == settings


def test_settings_rotation__default_value(test_data):
    prob = HyperPack(**test_data)
    assert prob._rotation == prob.ROTATION_DEFAULT_VALUE
    assert prob._settings == {}


def test_settings_rotation__change_value(test_data):
    prob = HyperPack(**test_data)
    assert prob._rotation == prob.ROTATION_DEFAULT_VALUE

    settings = {"rotation": False}
    prob.settings = settings
    assert prob._rotation is False

    prob = HyperPack(**test_data)
    prob.settings["rotation"] = False
    prob.validate_settings()
    assert prob._rotation is False
