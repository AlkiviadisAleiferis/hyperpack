import re

import pytest

from hyperpack import HyperPack
from hyperpack.benchmarks.datasets.hopper_and_turton_2000.C3 import containers, items_a

DEFAULT_POTENTIAL_POINTS_STRATEGY = HyperPack.DEFAULT_POTENTIAL_POINTS_STRATEGY


@pytest.mark.parametrize(
    "container,items,points_seq",
    [
        # Item 2 doesn't fit.
        (
            (2, 3),
            ((2, 3), (1, 1)),
            ("A", "B"),
        ),
    ],
)
def test_fitting(container, items, points_seq):
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert len(prob.solution["cont-0"]) == 1


def test_solve_doesnt_change_items_attribute(test_data):
    items = HyperPack._deepcopy_items(None, items_a)
    prob = HyperPack(**test_data)
    items = prob._deepcopy_items()
    prob.solve()
    assert prob.items == items
    assert id(prob.items) != id(items)


@pytest.mark.parametrize(
    "container,items,points_seq",
    [
        # Item 2 doesn't fit initially. Rotates.
        (
            (2, 3),
            ((1, 2), (3, 1)),
            ("B"),
        ),
    ],
)
def test_rotation_when_fiting(container, items, points_seq):
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    placement = (
        prob.solution["cont-0"]["i-1"][0],
        prob.solution["cont-0"]["i-1"][1],
    )
    assert placement == (1, 0)
