import pytest

from hyperpack import ContainersError, HyperPack, ItemsError, SettingsError, constants


@pytest.mark.parametrize(
    "settings,error_msg",
    [
        (
            {"workers_num": 0},
            SettingsError.WORKERS_NUM_VALUE,
        ),
        (
            {"workers_num": "str"},
            SettingsError.WORKERS_NUM_VALUE,
        ),
        (
            {"workers_num": [0]},
            SettingsError.WORKERS_NUM_VALUE,
        ),
        (
            {"workers_num": {"key": 0}},
            SettingsError.WORKERS_NUM_VALUE,
        ),
    ],
)
def test_settings_workers_num_validation_error(settings, error_msg, request):
    test_data = request.getfixturevalue("test_data")
    caplog = request.getfixturevalue("caplog")
    with pytest.raises(SettingsError) as exc_info:
        prob = HyperPack(**test_data, settings=settings)
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    items = {"test_id": {"w": 10, "l": 10}}
    containers = {"cont_id": {"W": 100, "L": 100}}
    prob = HyperPack(**test_data)

    # now tests for changing the _settings value
    with pytest.raises(SettingsError) as exc_info:
        prob.settings = settings
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


def test_settings_workers_num__ok(test_data):
    settings = {"workers_num": 5}
    prob = HyperPack(**test_data, settings=settings)
    assert prob._workers_num == 5
    assert prob.settings == settings


def test_settings_workers_num__default_value(test_data):
    prob = HyperPack(**test_data)
    assert prob._workers_num == prob.WORKERS_NUM_DEFAULT_VALUE
    assert prob._settings == {}


def test_settings_workers_num__change_value(test_data):
    prob = HyperPack(**test_data)

    settings = {"workers_num": 3}
    prob.settings = settings
    assert prob._workers_num == 3
    assert prob._settings == settings

    prob.settings["workers_num"] = 2
    prob.validate_settings()
    assert prob._workers_num == 2
    assert prob._settings == {"workers_num": 2}


def test_settings_warning_os(test_data, caplog, platform_os_mock):
    warning_msg = (
        "In Windows OS multiprocessing needs 'Entry point protection'"
        "\nwhich means adding if '__name__' == '__main__' before"
        " multiprocessing depending code execution"
    )
    settings = {"workers_num": 3}

    prob = HyperPack(**test_data, settings=settings)
    assert warning_msg in caplog.text

    # now tests for changing the _settings value
    prob = HyperPack(**test_data)
    prob.settings = settings
    assert warning_msg in caplog.text


def test_settings_max_workers_num_warning(test_data, caplog, cpu_count_mock):
    warning_msg = SettingsError.WORKERS_NUM_CPU_COUNT_WARNING
    settings = {"workers_num": 3}
    prob = HyperPack(**test_data, settings=settings)
    assert warning_msg in caplog.text

    # now tests for changing the _settings value
    prob = HyperPack(**test_data)
    prob.settings = settings
    assert warning_msg in caplog.text
