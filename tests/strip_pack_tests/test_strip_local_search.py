import os

import pytest

from hyperpack import HyperPack, SettingsError, DimensionsError, benchmarks
from tests.utils import (
    SOLUTION_LOG_ITEMS_STRATEGY,
    SOLUTION_STRING_CONTAINER,
    SOLUTION_STRING_REMAINING_ITEMS,
)

C3 = benchmarks.datasets.hopper_and_turton_2000.C3

STRIP_PACK_CONT_ID = HyperPack.STRIP_PACK_CONT_ID

POTENTIAL_POINTS_STRATEGY = (
    "B",
    "C",
    "D",
    "B_",
    "B__",
    "E",
    "F",
    "A__",
    "A_",
    "A",
)

# in local search searching procedure is deterministic
# always the same path will be followed if mechanics unchanged
# That leaves testing the ability to check valid behaviour
# container_height updated at every accepted solution

# container_min_height is None -> all items must be in solution
# container_min_height is not None -> not all items must be in solution


def test_reset_container_height():
    strip_pack_width = C3.containers["container_0"]["W"]
    prob = HyperPack(items=C3.items_a, strip_pack_width=strip_pack_width)
    prob.potential_points_strategy = POTENTIAL_POINTS_STRATEGY

    init_height = prob.container_height
    prob.container_min_height = 33
    prob.local_search()
    assert prob.container_height < init_height

    prob.reset_container_height()
    assert prob.container_height == init_height
    assert prob.container_min_height == None


def test_container_min_height_None():
    strip_pack_width = C3.containers["container_0"]["W"]
    prob = HyperPack(items=C3.items_a, strip_pack_width=strip_pack_width)
    prob.potential_points_strategy = POTENTIAL_POINTS_STRATEGY

    # ALL ITEMS IN SOLUTION TEST
    # container_min_height is None ->
    # all the items must be in every solution
    assert prob.container_height == strip_pack_width * prob.MAX_W_L_RATIO
    prob.local_search(debug=True)
    assert prob.container_height < (strip_pack_width * prob.MAX_W_L_RATIO)
    assert prob.container_height == 35
    assert [600, 44, 41, 39, 38, 37, 36, 35] == prob._heights_history
    # Check _get_container_height
    solution = prob.solution[STRIP_PACK_CONT_ID]
    height = max([solution[item_id][1] + solution[item_id][3] for item_id in solution])
    assert prob._get_container_height() == height
    # Check that all items in solution are ensured always
    assert len(C3.items_a) == len(prob.solution[STRIP_PACK_CONT_ID])

    # NO SOLUTION ACCEPTANCE TEST
    # container_min_height is None +
    # container_height too low
    # NO SOLUTION ACCEPTED IN LOCAL SEARCH BEYOND FIRST
    prob.container_height = 28
    prob.solve()
    solution = prob._deepcopy_solution()
    prob.local_search(debug=True)
    assert prob.container_height == 28
    assert solution == prob.solution
    assert [28] == prob._heights_history
    # Check _get_container_height
    assert prob._get_container_height() == 28


def test_container_min_height_not_None():
    strip_pack_width = C3.containers["container_0"]["W"]
    prob = HyperPack(items=C3.items_a, strip_pack_width=strip_pack_width)
    prob.potential_points_strategy = POTENTIAL_POINTS_STRATEGY

    # container_min_height == 32 -> not all the items must be in every solution
    prob._container_min_height = 32
    prob.local_search(debug=True)
    assert prob.container_height == 32
    # value set at local_search last node
    assert prob._get_container_height() == 32
    assert len(C3.items_a) > len(prob.solution[STRIP_PACK_CONT_ID])

    # container_min_height == 55 -> solution height is < 55
    # but _get_container_height returns 55 and container_height == 5
    prob._container_height = 111
    prob._container_min_height = 55
    prob.local_search(debug=True)
    assert prob.container_height == 55
    # shouldn't change
    assert prob._container_min_height == 55
    # value set at local_search last node
    assert prob._get_container_height() == 55
    assert len(C3.items_a) == len(prob.solution[STRIP_PACK_CONT_ID])


def test_doesnt_change_items():
    from copy import deepcopy

    settings = {"max_time_in_seconds": 10, "workers_num": 1, "figure": {"show": False}}
    strip_pack_width = C3.containers["container_0"]["W"]
    prob = HyperPack(items=C3.items_a, strip_pack_width=strip_pack_width)
    prob.potential_points_strategy = POTENTIAL_POINTS_STRATEGY

    items = prob.items.deepcopy()
    prob.local_search()
    assert prob.items == items


def test_doesnt_change_settings():
    from copy import deepcopy

    settings = {"max_time_in_seconds": 10, "workers_num": 1, "figure": {"show": False}}
    strip_pack_width = C3.containers["container_0"]["W"]
    prob = HyperPack(items=C3.items_a, strip_pack_width=strip_pack_width)
    prob.potential_points_strategy = POTENTIAL_POINTS_STRATEGY

    settings = deepcopy(prob.settings)
    prob.local_search()
    assert prob.settings == settings


def test_doesnt_change_containers():
    strip_pack_width = C3.containers["container_0"]["W"]
    prob = HyperPack(items=C3.items_a, strip_pack_width=strip_pack_width)
    prob.potential_points_strategy = POTENTIAL_POINTS_STRATEGY

    containers = prob.containers.deepcopy()
    prob.local_search()
    assert prob.containers == containers


def test_log_solution():
    strip_pack_width = C3.containers["container_0"]["W"]
    prob = HyperPack(items=C3.items_a, strip_pack_width=strip_pack_width)
    prob.potential_points_strategy = POTENTIAL_POINTS_STRATEGY

    prob.local_search()

    solution_log = SOLUTION_LOG_ITEMS_STRATEGY.format(100)
    solution_log += SOLUTION_STRING_CONTAINER.format(STRIP_PACK_CONT_ID, 60, 35, 85.7143)
    solution = prob.solution[STRIP_PACK_CONT_ID]
    # height of items stack in solution
    max_height = max([solution[item_id][1] + solution[item_id][3] for item_id in solution])
    solution_log += f"\t[max height] : {max_height}"
    solution_log += SOLUTION_STRING_REMAINING_ITEMS.format([])
    solution_log = solution_log.replace("\n", "").replace("\t", "")

    print(solution_log)
    print(prob.log_solution().replace("\n", "").replace("\t", ""))
    assert prob.log_solution().replace("\n", "").replace("\t", "") == solution_log
