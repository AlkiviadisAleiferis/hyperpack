import pytest

from hyperpack import HyperPack, SettingsError


@pytest.mark.parametrize(
    "settings,error_msg",
    [
        (
            {"max_time_in_seconds": 0},
            SettingsError.MAX_TIME_IN_SECONDS_VALUE,
        ),
        (
            {"max_time_in_seconds": "str"},
            SettingsError.MAX_TIME_IN_SECONDS_TYPE,
        ),
        (
            {"max_time_in_seconds": [0]},
            SettingsError.MAX_TIME_IN_SECONDS_TYPE,
        ),
        (
            {"max_time_in_seconds": {"key": 0}},
            SettingsError.MAX_TIME_IN_SECONDS_TYPE,
        ),
        (
            {"max_time_in_seconds": 1.1},
            SettingsError.MAX_TIME_IN_SECONDS_TYPE,
        ),
    ],
)
def test_settings_max_time_in_seconds_validation_error(settings, error_msg, request):
    items = {"id": {"w": 10, "l": 10}}
    containers = {"cont_id": {"W": 100, "L": 100}}
    caplog = request.getfixturevalue("caplog")
    with pytest.raises(SettingsError) as exc_info:
        prob = HyperPack(containers=containers, items=items, settings=settings)
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    # now tests for changing the _settings value
    proper_settings = {}
    prob = HyperPack(containers=containers, items=items, settings=proper_settings)
    caplog = request.getfixturevalue("caplog")
    with pytest.raises(SettingsError) as exc_info:
        prob.settings = settings
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


def test_settings_max_time_in_seconds__ok(test_data):
    settings = {"max_time_in_seconds": 5}
    prob = HyperPack(**test_data, settings=settings)
    assert prob._max_time_in_seconds == 5
    assert prob.settings == settings


def test_settings_max_time_in_seconds__deafult_value(test_data):
    prob = HyperPack(**test_data)
    assert prob._max_time_in_seconds == HyperPack.MAX_TIME_IN_SECONDS_DEFAULT_VALUE
    assert prob.settings == {}


def test_settings_max_time_in_seconds__change_value(test_data):
    prob = HyperPack(**test_data)
    settings = {"max_time_in_seconds": 3}
    prob.settings = settings
    assert prob._max_time_in_seconds == 3
    assert prob.settings == settings

    prob.settings["max_time_in_seconds"] = 2
    prob.validate_settings()
    assert prob._max_time_in_seconds == 2
    assert prob.settings == {"max_time_in_seconds": 2}
