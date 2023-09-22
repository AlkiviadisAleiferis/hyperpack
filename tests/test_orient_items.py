import re

import pytest

from hyperpack import HyperPack

DEFAULT_POTENTIAL_POINTS_STRATEGY = HyperPack.DEFAULT_POTENTIAL_POINTS_STRATEGY


@pytest.mark.parametrize(
    "orientation",
    ["wide", "long"],
)
def test_orient_items(orientation, request):
    items = ((2, 3), (12, 3), (12, 14), (1, 1), (4, 6), (7, 9), (1, 2))
    containers = {"cont-0": {"W": 55, "L": 55}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items)
    items = prob._deepcopy_items()
    init_items = prob._deepcopy_items()

    return_value = prob.orient_items(orientation=orientation)
    assert return_value is None
    assert list(prob.items.items()) != list(init_items.items())
    for _, item in prob.items.items():
        if orientation == "wide":
            assert item["w"] >= item["l"]
        else:
            assert item["w"] <= item["l"]


def test_orient_items__no_rotation_warning(caplog):
    settings = {"rotation": False}
    items = ((2, 3), (12, 3), (12, 14), (1, 1), (4, 6), (7, 9), (1, 2))
    containers = {"cont-0": {"W": 55, "L": 55}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    return_value = prob.orient_items()
    assert items == prob.items
    assert "can't rotate items. Rotation is disabled" in caplog.text
    assert return_value is None


def test_orient_items__wrong_orientation_parameter(caplog):
    items = ((2, 3), (12, 3), (12, 14), (1, 1), (4, 6), (7, 9), (1, 2))
    containers = {"cont-0": {"W": 55, "L": 55}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items)
    orientation = "wrong_param"
    return_value = prob.orient_items(orientation=orientation)
    assert items == prob.items
    assert (
        f"orientation parameter '{orientation}' not valid. Orientation skipped." in caplog.text
    )
    assert return_value is None


def test_orient_items__orientation_None(caplog):
    items = ((2, 3), (12, 3), (12, 14), (1, 1), (4, 6), (7, 9), (1, 2))
    containers = {"cont-0": {"W": 55, "L": 55}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items)
    return_value = prob.orient_items(orientation=None)
    assert items == prob.items
    assert f"orientation parameter '{None}' not valid. Orientation skipped." not in caplog.text
    assert return_value is None
