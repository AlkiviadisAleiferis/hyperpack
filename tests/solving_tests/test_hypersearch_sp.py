import pytest

from hyperpack import HyperPack
from hyperpack.benchmarks.datasets.hopper_and_turton_2000.C3 import containers, items_a
from tests.utils import (
    SOLUTION_LOG_ITEMS_STRATEGY,
    SOLUTION_STRING_CONTAINER,
    SOLUTION_STRING_REMAINING_ITEMS,
)

DEFAULT_POTENTIAL_POINTS_STRATEGY = HyperPack.DEFAULT_POTENTIAL_POINTS_STRATEGY


def test_non_exhaustive_max_obj_value(caplog):
    prob = HyperPack(containers=containers, items=items_a)
    prob.sort_items(sorting_by=("area", True))
    prob.orient_items(orientation="wide")
    prob.hypersearch(_exhaustive=False)
    solution_log = SOLUTION_LOG_ITEMS_STRATEGY.format(
        100,
    )
    solution_log += SOLUTION_STRING_CONTAINER.format("container_0", 60, 30, 100)
    solution_log += SOLUTION_STRING_REMAINING_ITEMS.format([])
    solution_log = solution_log.replace("\n", "").replace("\t", "")
    assert prob.calculate_obj_value() == 1.0000000000000002
    assert len(prob.solution["container_0"]) == len(items_a)
    assert prob.log_solution().replace("\n", "").replace("\t", "") == solution_log
    assert "Solving with single core" in caplog.text


def test_sorts_items():
    # only sorting and orientation can change items not hypersearch itself
    # also tested that hypersearch orients and sorts items
    settings = {"max_time_in_seconds": 1}
    containers = {"c_a": {"W": 25, "L": 25}, "c_b": {"W": 25, "L": 20}}
    prob = HyperPack(containers=containers, items=items_a, settings=settings)
    prob.sort_items()
    prob.orient_items()
    items = prob._deepcopy_items()
    prob.hypersearch()
    assert prob.items == items


def test_orientation_sorting_skip():
    # only sorting and orientation can change items# not hypersearch itself
    settings = {"max_time_in_seconds": 1}
    containers = {"c_a": {"W": 25, "L": 25}, "c_b": {"W": 25, "L": 20}}
    items = HyperPack._deepcopy_items(None, items_a)
    prob = HyperPack(containers=containers, items=items, settings=settings)
    items = prob._deepcopy_items()
    prob.hypersearch(orientation=None, sorting_by=None)
    assert prob.items == items
    assert id(prob.items) != id(items)


def test_two_bins_solution(caplog):
    containers = {"c_a": {"W": 25, "L": 25}, "c_b": {"W": 25, "L": 20}}
    prob = HyperPack(containers=containers, items=items_a)
    prob.hypersearch(_exhaustive=False)
    solution_log = SOLUTION_LOG_ITEMS_STRATEGY.format(
        53.5714,
        ["B_", "C", "A", "A_", "B", "D", "A__", "B__", "F", "E"],
    )
    solution_log += SOLUTION_STRING_CONTAINER.format("c_a", 25, 25, 100)
    solution_log += SOLUTION_STRING_CONTAINER.format("c_b", 25, 20, 99.2)
    solution_log += SOLUTION_STRING_REMAINING_ITEMS.format(
        [
            "i_6",
            "i_25",
            "i_24",
            "i_7",
            "i_1",
            "i_12",
            "i_15",
            "i_13",
            "i_8",
            "i_14",
            "i_27",
            "i_23",
            "i_21",
        ]
    )
    solution_log = solution_log.replace("\n", "").replace("\t", "")
    solution_log_output = prob.log_solution().replace("\n", "").replace("\t", "")
    assert prob.calculate_obj_value() == 1.6944000000000004
    assert solution_log_output == solution_log
    assert "Solving with single core" in caplog.text


def test_two_bins_no_solution():
    containers = {"c_a": {"W": 1, "L": 1}}
    prob = HyperPack(containers=containers, items={"a": {"w": 2, "l": 2}})
    prob.hypersearch(_exhaustive=False)
    assert prob.solution == {"c_a": {}}


def test_doesnt_change_settings():
    from copy import deepcopy

    settings = {"max_time_in_seconds": 10, "workers_num": 1, "figure": {"show": False}}
    containers = {"c_a": {"W": 1, "L": 1}}
    prob = HyperPack(containers=containers, items={"a": {"w": 2, "l": 2}})
    settings = deepcopy(prob.settings)
    prob.hypersearch()
    assert prob.settings == settings


def test_doesnt_change_containers(test_data):
    prob = HyperPack(**test_data)
    containers = prob.containers.deepcopy()
    prob.hypersearch()
    assert prob.containers == containers
