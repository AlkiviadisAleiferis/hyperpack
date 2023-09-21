import os
from pathlib import Path

import pytest

from hyperpack import FigureExportError, HyperPack

PROBLEM_DATA = (
    ((1, 2), (3, 1), (3, 3)),
    ((1, 2), (3, 1), (2, 2)),
    ("B",),
)


@pytest.mark.parametrize(
    "figure_settings",
    [
        {
            "figure": {
                "show": False,
                "export": {
                    "type": "html",
                },
            }
        },
        {
            "figure": {
                "show": False,
                "export": {
                    "type": "image",
                    "format": "png",
                },
            }
        },
        {
            "figure": {
                "show": False,
                "export": {
                    "type": "image",
                    "format": "pdf",
                },
            }
        },
        {
            "figure": {
                "show": False,
                "export": {
                    "type": "image",
                    "format": "jpeg",
                },
            }
        },
        {
            "figure": {
                "show": False,
                "export": {
                    "type": "image",
                    "format": "webp",
                },
            }
        },
        {
            "figure": {
                "show": False,
                "export": {
                    "type": "image",
                    "format": "svg",
                },
            }
        },
    ],
)
def test_figure_exportation__no_file_name(figure_settings, request):
    containers, items, points_seq = PROBLEM_DATA
    d = request.getfixturevalue("tmp_path") / "figures"
    d.mkdir()
    settings = {
        "workers_num": 1,
    }
    settings.update(figure_settings)
    settings["figure"]["export"].update({"path": str(d)})

    export_type = settings["figure"]["export"]["type"]
    if export_type == "html":
        file_format = "html"
    else:
        file_format = settings["figure"]["export"]["format"]
    file_name = settings["figure"]["export"].get("file_name", "PlotlyGraph")

    containers = {
        f"cont-{i}": {"W": container[0], "L": container[1]}
        for i, container in enumerate(containers)
    }
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}

    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob.potential_points_strategy = points_seq
    prob.solve()
    prob.create_figure()

    for cont_id in containers:
        assert (d / f"{file_name}__{cont_id}.{file_format}").exists()


@pytest.mark.parametrize(
    "figure_settings",
    [
        {
            "figure": {
                "show": False,
                "export": {
                    "type": "html",
                    "file_name": "pytest",
                },
            }
        },
        {
            "figure": {
                "show": False,
                "export": {
                    "type": "image",
                    "format": "png",
                    "file_name": "pytest",
                },
            }
        },
        {
            "figure": {
                "show": False,
                "export": {
                    "type": "image",
                    "format": "pdf",
                    "file_name": "pytest",
                },
            }
        },
        {
            "figure": {
                "show": False,
                "export": {
                    "type": "image",
                    "format": "jpeg",
                    "file_name": "pytest",
                },
            }
        },
        {
            "figure": {
                "show": False,
                "export": {
                    "type": "image",
                    "format": "webp",
                    "file_name": "pytest",
                },
            }
        },
        {
            "figure": {
                "show": False,
                "export": {
                    "type": "image",
                    "format": "svg",
                    "file_name": "pytest",
                },
            }
        },
    ],
)
def test_figure_exportation__file_name(figure_settings, request):
    containers, items, points_seq = PROBLEM_DATA
    d = request.getfixturevalue("tmp_path") / "figures"
    d.mkdir()
    settings = {
        "workers_num": 1,
    }
    settings.update(figure_settings)
    settings["figure"]["export"].update({"path": str(d)})

    export_type = settings["figure"]["export"]["type"]
    if export_type == "html":
        file_format = "html"
    else:
        file_format = settings["figure"]["export"]["format"]
    file_name = settings["figure"]["export"].get("file_name", "PlotlyGraph")

    containers = {
        f"cont-{i}": {"W": container[0], "L": container[1]}
        for i, container in enumerate(containers)
    }
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}

    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob.potential_points_strategy = points_seq
    prob.solve()
    prob.create_figure()

    for cont_id in containers:
        assert (d / f"{file_name}__{cont_id}.{file_format}").exists()


def test_figure_no_solution_found(test_data, caplog):
    prob = HyperPack(**test_data)
    prob.create_figure()
    assert FigureExportError.NO_SOLUTION_WARNING in caplog.text


def test_figure_no_operation_warning(test_data, caplog):
    prob = HyperPack(**test_data, settings={})
    prob.solve()
    prob.create_figure()
    assert FigureExportError.NO_FIGURE_OPERATION in caplog.text


def test_figure_FigureExportError(test_data):
    prob = HyperPack(**test_data)
    prob.solve()
    prob._settings = {
        "figure": {
            "show": False,
            "export": {
                "type": "image",
                "format": "png",
                "file_name": "pytest",
            },
        }
    }
    with pytest.raises(FigureExportError) as exc_info:
        prob.create_figure()
