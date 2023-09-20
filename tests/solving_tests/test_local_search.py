import pytest

from hyperpack import HyperPack
from hyperpack.benchmarks.datasets.hopper_and_turton_2000.C3 import containers, items_a
from tests.utils import (
    SOLUTION_LOG_ITEMS_STRATEGY,
    SOLUTION_STRING_CONTAINER,
    SOLUTION_STRING_REMAINING_ITEMS,
)

DEFAULT_POTENTIAL_POINTS_STRATEGY = HyperPack.DEFAULT_POTENTIAL_POINTS_STRATEGY


def test_local_search_max_value(caplog):
    settings = {"workers_num": 1}
    prob = HyperPack(containers=containers, items=items_a, settings=settings)
    prob._potential_points_strategy = [
        "B_",
        "C",
        "A",
        "A_",
        "B",
        "D",
        "A__",
        "B__",
        "F",
        "E",
    ]
    prob.sort_items(sorting_by=("area", True))
    prob.orient_items(orientation="wide")
    prob.local_search()
    solution_log = SOLUTION_LOG_ITEMS_STRATEGY.format(
        100,
        ["B_", "C", "A", "A_", "B", "D", "A__", "B__", "F", "E"],
    )
    solution_log += SOLUTION_STRING_CONTAINER.format("container_0", 60, 30, 100)
    solution_log += SOLUTION_STRING_REMAINING_ITEMS.format([])
    solution_log = solution_log.replace("\n", "").replace("\t", "")
    assert prob._calc_obj_value() == 1.0000000000000002
    assert len(prob.solution["container_0"]) == len(items_a)
    assert prob.log_solution().replace("\n", "").replace("\t", "") == solution_log


def test_local_search_two_bins():
    settings = {"workers_num": 1}
    containers = {"c_a": {"W": 25, "L": 25}, "c_b": {"W": 25, "L": 20}}
    items = HyperPack._deepcopy_items(None, items_a)
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob.local_search()

    solution_log = SOLUTION_LOG_ITEMS_STRATEGY.format(
        67.8571,
        ("A", "B", "C", "D", "A_", "B_", "B__", "A__", "E", "F"),
    )
    solution_log += SOLUTION_STRING_CONTAINER.format("c_a", 25, 25, 99.36)
    solution_log += SOLUTION_STRING_CONTAINER.format("c_b", 25, 20, 98.8)
    solution_log += SOLUTION_STRING_REMAINING_ITEMS.format(
        ["i_10", "i_11", "i_16", "i_19", "i_20", "i_24", "i_25", "i_26", "i_27"]
    )
    solution_log = solution_log.replace("\n", "").replace("\t", "")
    solution_log_output = prob.log_solution().replace("\n", "").replace("\t", "")
    assert prob._calc_obj_value() == 1.6852
    assert solution_log_output == solution_log


def test_throttle(caplog):
    # if value is changed, change test accordingly
    assert HyperPack.MAX_NEIGHBORS_THROTTLE == 2500

    containers = {"cont-0": {"W": 1, "L": 1}}
    items = {f"i-{i}": {"w": 2, "l": 2} for i in range(73)}
    prob = HyperPack(containers=containers, items=items)
    prob.local_search(debug=True)

    assert "processed_neighbors : 2500" in caplog.text

    containers = {"cont-0": {"W": 1, "L": 1}}
    items = {f"i-{i}": {"w": 2, "l": 2} for i in range(70)}
    prob = HyperPack(containers=containers, items=items)
    prob.local_search(debug=True)

    assert "processed_neighbors : 2415" in caplog.text


def test_local_search_doesnt_change_items_attribute():
    settings = {"workers_num": 1}
    containers = {"c_a": {"W": 25, "L": 25}, "c_b": {"W": 25, "L": 20}}
    items = HyperPack._deepcopy_items(None, items_a)
    prob = HyperPack(containers=containers, items=items, settings=settings)
    items = prob._deepcopy_items()
    prob.local_search()
    assert prob.items == items


def test_local_search_singlecore_no_solution(caplog):
    settings = {"workers_num": 1}
    containers = {"c_a": {"W": 1, "L": 1}}
    prob = HyperPack(
        containers=containers, items={"a": {"w": 2, "l": 2}}, settings=settings
    )
    prob.local_search()
    assert prob.solution == {"c_a": {}}
