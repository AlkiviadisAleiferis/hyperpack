"""
Serious Note:
The tests inside this module must be run alone like this:
pytest tests/test_multiprocess.py::test_name
because multiprocessing demands safe guarding with
if "__name__" == "__main__:"
"""
import re

import pytest

from hyperpack import HyperPack, exceptions
from hyperpack.benchmarks.datasets.hopper_and_turton_2000.C3 import (
    containers as C3_containers,
)
from hyperpack.benchmarks.datasets.hopper_and_turton_2000.C3 import items_a
from tests.utils import (
    SOLUTION_LOG_ITEMS_STRATEGY,
    SOLUTION_STRING_CONTAINER,
    SOLUTION_STRING_REMAINING_ITEMS,
)


def test_hypersearch_two_bins_multicore(caplog):
    settings = {"workers_num": 2}
    containers = {"c_a": {"W": 25, "L": 25}, "c_b": {"W": 25, "L": 20}}
    prob = HyperPack(containers=containers, items=items_a, settings=settings)
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
    print(solution_log)
    print(prob.log_solution().replace("\n", "").replace("\t", ""))
    r = re.compile(r"Winning Process hypersearch_[\d] found max")
    assert prob._calc_obj_value() == 1.6944000000000004
    assert prob.log_solution().replace("\n", "").replace("\t", "") == solution_log
    assert r.search(caplog.text)


def test_hypersearch_multicore_exhaustive_max_time(caplog):
    settings = {"workers_num": 2, "max_time_in_seconds": 5}
    prob = HyperPack(containers=C3_containers, items=items_a, settings=settings)
    prob.sort_items(sorting_by=("area", True))
    prob.orient_items(orientation="wide")
    prob.hypersearch()
    r = re.compile(r"Winning Process hypersearch_[\d] found max")
    r_total_time = re.compile(r"Execution time : (\d)\.(\d+) \[sec\]")
    s, ms = r_total_time.search(caplog.text).groups()
    # assertion might fail depending on testing machine
    assert int(s) < 8
    assert r.search(caplog.text)


def test_hypersearch_multicore_non_exhaustive_max_obj_value(caplog):
    settings = {"workers_num": 2}
    prob = HyperPack(containers=C3_containers, items=items_a, settings=settings)
    prob.sort_items(sorting_by=("area", True))
    prob.orient_items(orientation="wide")
    prob.hypersearch(_exhaustive=False)
    solution_log = SOLUTION_LOG_ITEMS_STRATEGY.format(
        100,
        ["B_", "C", "A", "A_", "B", "D", "A__", "B__", "F", "E"],
    )
    solution_log += SOLUTION_STRING_CONTAINER.format("container_0", 60, 30, 100)
    solution_log += SOLUTION_STRING_REMAINING_ITEMS.format([])
    solution_log = solution_log.replace("\n", "").replace("\t", "")
    r = re.compile(r"Winning Process hypersearch_[\d] found max")
    print(solution_log)
    print(prob.log_solution().replace("\n", "").replace("\t", ""))
    assert prob._calc_obj_value() == 1.0000000000000002
    assert len(prob.solution["container_0"]) == len(items_a)
    assert prob.log_solution().replace("\n", "").replace("\t", "") == solution_log
    assert r.search(caplog.text)


def test_hypersearch_multicore_no_solution(caplog):
    settings = {"workers_num": 2}
    prob = HyperPack(
        containers={"c-0": {"W": 1, "L": 1}, "c-1": {"W": 1, "L": 1}},
        items={"i-0": {"w": 2, "l": 2}},
        settings=settings,
    )
    prob.hypersearch(_exhaustive=False)
    solution_log = SOLUTION_LOG_ITEMS_STRATEGY.format(
        0,
        None,
    )
    solution_log += SOLUTION_STRING_CONTAINER.format("c-0", 1, 1, 0)
    solution_log += SOLUTION_STRING_CONTAINER.format("c-1", 1, 1, 0)
    solution_log += SOLUTION_STRING_REMAINING_ITEMS.format(["i-0"])
    solution_log = solution_log.replace("\n", "").replace("\t", "")
    r = re.compile(r"Winning Process hypersearch_[\d] found max")
    print(solution_log)
    print(prob.log_solution().replace("\n", "").replace("\t", ""))
    assert prob._calc_obj_value() == 0
    assert len(prob.solution["c-0"]) == 0
    assert len(prob.solution["c-1"]) == 0
    assert prob.log_solution().replace("\n", "").replace("\t", "") == solution_log
    assert r.search(caplog.text)


def test_hypersearch_multicore_force_error_on_first_process(caplog):
    settings = {"workers_num": 2}
    prob = HyperPack(
        containers={"c-0": {"W": 1, "L": 1}, "c-1": {"W": 1, "L": 1}},
        items={"i-0": {"w": 2, "l": 2}},
        settings=settings,
    )
    prob.hypersearch(_exhaustive=False, _force_raise_error_index=0)
    assert "Some of the processes raised an exception. Please check logs." in caplog.text
    assert "sequence = None" in caplog.text
    solution_log = SOLUTION_LOG_ITEMS_STRATEGY.format(
        0,
        None,
    )
    solution_log += SOLUTION_STRING_CONTAINER.format("c-0", 1, 1, 0)
    solution_log += SOLUTION_STRING_CONTAINER.format("c-1", 1, 1, 0)
    solution_log += SOLUTION_STRING_REMAINING_ITEMS.format(["i-0"])
    solution_log = solution_log.replace("\n", "").replace("\t", "")
    r = re.compile(r"Winning Process hypersearch_[\d] found max")
    print(solution_log)
    print(prob.log_solution().replace("\n", "").replace("\t", ""))
    assert prob._calc_obj_value() == 0
    assert len(prob.solution["c-0"]) == 0
    assert len(prob.solution["c-1"]) == 0
    assert prob.log_solution().replace("\n", "").replace("\t", "") == solution_log
    assert r.search(caplog.text)


def test_hypersearch_multicore_all_processes_fail(caplog):
    settings = {"workers_num": 2}
    prob = HyperPack(
        containers={"c-0": {"W": 1, "L": 1}, "c-1": {"W": 1, "L": 1}},
        items={"i-0": {"w": 2, "l": 2}},
        settings=settings,
    )
    with pytest.raises(exceptions.MultiProcessError) as exc_info:
        prob.hypersearch(_exhaustive=False, _force_raise_error_index="all")
    assert exceptions.MultiProcessError.ALL_PROCESSES_FAILED == str(exc_info.value)
    assert exceptions.MultiProcessError.ALL_PROCESSES_FAILED in caplog.text


def test_hypersearch_multicore_doesnt_change_items():
    # only sorting and orientation can change items# not hypersearch itself
    # also tested that hypersearch orients and sorts items
    settings = {"workers_num": 2, "max_time_in_seconds": 3}
    containers = {"c_a": {"W": 25, "L": 25}, "c_b": {"W": 25, "L": 20}}
    items = HyperPack._deepcopy_items(None, items_a)
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob.sort_items()
    prob.orient_items()
    items = prob._deepcopy_items()
    prob.hypersearch()
    assert prob.items == items


def test_hypersearch_multicore_orientation_sorting_skip():
    # only sorting and orientation can change items# not hypersearch itself
    settings = {"workers_num": 2, "max_time_in_seconds": 3}
    containers = {"c_a": {"W": 25, "L": 25}, "c_b": {"W": 25, "L": 20}}
    items = HyperPack._deepcopy_items(None, items_a)
    prob = HyperPack(containers=containers, items=items, settings=settings)
    items = prob._deepcopy_items()
    prob.hypersearch(orientation=None, sorting_by=None)
    assert prob.items == items
