import re

import pytest

from hyperpack import HyperPack

DEFAULT_POTENTIAL_POINTS_STRATEGY = HyperPack.DEFAULT_POTENTIAL_POINTS_STRATEGY


@pytest.mark.parametrize(
    "sorting_by",
    [
        ("area", True),
        ("perimeter", True),
        ("longest_side_ratio", True),
        ("area", False),
        ("perimeter", False),
        ("longest_side_ratio", False),
        ("NotImplemented", None),
    ],
)
def test_sorting(sorting_by):
    items = ((2, 3), (12, 3), (12, 14), (1, 1), (4, 6), (7, 9), (1, 2))
    containers = {"cont-0": {"W": 55, "L": 55}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items)

    by, reverse = sorting_by
    init_items = prob._deepcopy_items(items)

    if by == "NotImplemented":
        with pytest.raises(NotImplementedError):
            prob.sort_items(sorting_by=sorting_by)
        return

    prob.sort_items(sorting_by=sorting_by)
    assert list(prob.items.items()) != list(init_items.items())
    first_item = list(prob.items.items())[0]
    if by == "area":
        previous_quantity = first_item[1]["w"] * first_item[1]["l"]
    elif by == "perimeter":
        previous_quantity = first_item[1]["w"] * 2 + first_item[1]["l"] * 2
    elif by == "longest_side_ratio":
        previous_quantity = max(first_item[1]["w"], first_item[1]["l"]) / min(
            first_item[1]["w"], first_item[1]["l"]
        )

    for _, item in list(prob.items.items())[1:]:
        if by == "area":
            quantity = item["w"] * item["l"]
        elif by == "perimeter":
            quantity = item["w"] * 2 + item["l"] * 2
        elif by == "longest_side_ratio":
            quantity = max(item["w"], item["l"]) / min(item["w"], item["l"])

        if reverse:
            assert quantity <= previous_quantity
        else:
            assert quantity >= previous_quantity

        previous_quantity = quantity

    assert prob.items.__class__.__name__ == "Items"


def test_sorting_by_None(caplog):
    items = ((2, 3), (12, 3), (12, 14), (1, 1), (4, 6), (7, 9), (1, 2))
    containers = {"cont-0": {"W": 100, "L": 100}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items)

    ret = prob.sort_items(sorting_by=None)
    assert ret == None
