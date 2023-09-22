import os
from pathlib import Path

import pytest

from hyperpack import HyperPack, SettingsError

LIB_PATH = os.getcwd()


@pytest.mark.parametrize(
    "settings,error_msg",
    [
        # figure
        ({"figure": None}, SettingsError.FIGURE_KEY_TYPE),
        ({"figure": "str"}, SettingsError.FIGURE_KEY_TYPE),
        ({"figure": []}, SettingsError.FIGURE_KEY_TYPE),
        ({"figure": 1}, SettingsError.FIGURE_KEY_TYPE),
        ({"figure": 1.2}, SettingsError.FIGURE_KEY_TYPE),
        ({"figure": set()}, SettingsError.FIGURE_KEY_TYPE),
        # export value
        ({"figure": {"export": None}}, SettingsError.FIGURE_EXPORT_VALUE_TYPE),
        (
            {"figure": {"export": "str"}},
            SettingsError.FIGURE_EXPORT_VALUE_TYPE,
        ),
        ({"figure": {"export": []}}, SettingsError.FIGURE_EXPORT_VALUE_TYPE),
        ({"figure": {"export": 1}}, SettingsError.FIGURE_EXPORT_VALUE_TYPE),
        ({"figure": {"export": 1.2}}, SettingsError.FIGURE_EXPORT_VALUE_TYPE),
        (
            {"figure": {"export": set()}},
            SettingsError.FIGURE_EXPORT_VALUE_TYPE,
        ),
        # export --> type
        (
            {"figure": {"export": {"type": None}}},
            SettingsError.FIGURE_EXPORT_TYPE_MISSING,
        ),
        (
            {"figure": {"export": {"type": {}}}},
            SettingsError.FIGURE_EXPORT_TYPE_VALUE,
        ),
        (
            {"figure": {"export": {"type": []}}},
            SettingsError.FIGURE_EXPORT_TYPE_VALUE,
        ),
        (
            {"figure": {"export": {"type": 1}}},
            SettingsError.FIGURE_EXPORT_TYPE_VALUE,
        ),
        (
            {"figure": {"export": {"type": 1.2}}},
            SettingsError.FIGURE_EXPORT_TYPE_VALUE,
        ),
        (
            {"figure": {"export": {"type": set()}}},
            SettingsError.FIGURE_EXPORT_TYPE_VALUE,
        ),
        (
            {"figure": {"export": {"type": "not_html_or_image"}}},
            SettingsError.FIGURE_EXPORT_TYPE_VALUE,
        ),
        # export --> path
        (
            {"figure": {"export": {"type": "html", "path": None}}},
            SettingsError.FIGURE_EXPORT_PATH_MISSING,
        ),
        (
            {"figure": {"export": {"type": "html", "path": 1}}},
            SettingsError.FIGURE_EXPORT_PATH_VALUE,
        ),
        (
            {"figure": {"export": {"type": "html", "path": 1.1}}},
            SettingsError.FIGURE_EXPORT_PATH_VALUE,
        ),
        (
            {"figure": {"export": {"type": "html", "path": [None]}}},
            SettingsError.FIGURE_EXPORT_PATH_VALUE,
        ),
        (
            {"figure": {"export": {"type": "html", "path": {}}}},
            SettingsError.FIGURE_EXPORT_PATH_VALUE,
        ),
        (
            {"figure": {"export": {"type": "html", "path": "non_existing_path"}}},
            SettingsError.FIGURE_EXPORT_PATH_NOT_EXISTS,
        ),
        (
            {
                "figure": {
                    "export": {
                        "type": "html",
                        "path": str(Path(os.getcwd()) / "LICENSE"),
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_PATH_NOT_DIRECTORY,
        ),
        # export --> format
        (
            {"figure": {"export": {"type": "image", "path": LIB_PATH}}},
            SettingsError.FIGURE_EXPORT_FORMAT_MISSING,
        ),
        (
            {"figure": {"export": {"type": "image", "path": LIB_PATH, "format": None}}},
            SettingsError.FIGURE_EXPORT_FORMAT_MISSING,
        ),
        (
            {"figure": {"export": {"type": "image", "path": LIB_PATH, "format": [None]}}},
            SettingsError.FIGURE_EXPORT_FORMAT_TYPE,
        ),
        (
            {"figure": {"export": {"type": "image", "path": LIB_PATH, "format": 1}}},
            SettingsError.FIGURE_EXPORT_FORMAT_TYPE,
        ),
        (
            {"figure": {"export": {"type": "image", "path": LIB_PATH, "format": 1.2}}},
            SettingsError.FIGURE_EXPORT_FORMAT_TYPE,
        ),
        (
            {"figure": {"export": {"type": "image", "path": LIB_PATH, "format": {}}}},
            SettingsError.FIGURE_EXPORT_FORMAT_TYPE,
        ),
        (
            {"figure": {"export": {"type": "image", "path": LIB_PATH, "format": "unknown"}}},
            SettingsError.FIGURE_EXPORT_FORMAT_VALUE,
        ),
        # export --> file_name
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": 1,
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_FILE_NAME_TYPE,
        ),
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": 1.1,
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_FILE_NAME_TYPE,
        ),
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": ["lst"],
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_FILE_NAME_TYPE,
        ),
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": {},
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_FILE_NAME_TYPE,
        ),
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": "$",
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_FILE_NAME_VALUE,
        ),
        # export --> image settings
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": "okay_name",
                        "width": 0,
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_WIDTH_VALUE,
        ),
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": "okay_name",
                        "width": "0",
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_WIDTH_VALUE,
        ),
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": "okay_name",
                        "width": [0],
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_WIDTH_VALUE,
        ),
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": "okay_name",
                        "width": {},
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_WIDTH_VALUE,
        ),
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": "okay_name",
                        "width": 1000,
                        "height": 0,
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_HEIGHT_VALUE,
        ),
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": "okay_name",
                        "width": 1000,
                        "height": "0",
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_HEIGHT_VALUE,
        ),
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": "okay_name",
                        "width": 1000,
                        "height": [0],
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_HEIGHT_VALUE,
        ),
        (
            {
                "figure": {
                    "export": {
                        "type": "image",
                        "path": LIB_PATH,
                        "format": "png",
                        "file_name": "okay_name",
                        "width": 1000,
                        "height": {},
                    }
                }
            },
            SettingsError.FIGURE_EXPORT_HEIGHT_VALUE,
        ),
        # show
        (
            {"figure": {"show": None}},
            SettingsError.FIGURE_SHOW_VALUE,
        ),
        (
            {"figure": {"show": "None"}},
            SettingsError.FIGURE_SHOW_VALUE,
        ),
        (
            {"figure": {"show": []}},
            SettingsError.FIGURE_SHOW_VALUE,
        ),
        (
            {"figure": {"show": {}}},
            SettingsError.FIGURE_SHOW_VALUE,
        ),
    ],
)
def test_settings_figure_validation(settings, error_msg, request):
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

    # now tests for changing the settings "figure" key
    prob = HyperPack(**test_data)
    caplog = request.getfixturevalue("caplog")
    with pytest.raises(SettingsError) as exc_info:
        prob.settings["figure"] = settings["figure"]
        prob.validate_settings()
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text
