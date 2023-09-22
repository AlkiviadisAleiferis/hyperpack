import os

import pytest

from hyperpack import HyperPack, benchmarks, HyperSearchProcess, constants

C3 = benchmarks.datasets.hopper_and_turton_2000.C3

STRIP_PACK_CONT_ID = HyperPack.STRIP_PACK_CONT_ID


def test_container_min_height_None(caplog):
    strip_pack_width = C3.containers["container_0"]["W"]
    settings = {"max_time_in_seconds": 1}
    prob = HyperPack(items=C3.items_a, strip_pack_width=strip_pack_width, settings=settings)

    # ALL TIMES IN SOLUTION TEST
    # container_min_height is None -> all the items must be in every solution
    prob.hypersearch()
    assert prob._get_container_height() < (strip_pack_width * prob.MAX_W_L_RATIO)
    solution = prob.solution[STRIP_PACK_CONT_ID]
    height = max([solution[item_id][1] + solution[item_id][3] for item_id in solution])
    assert prob._get_container_height() == height
    assert len(C3.items_a) == len(prob.solution[STRIP_PACK_CONT_ID])

    # NO SOLUTION ACCEPTANCE TEST
    # container_min_height is None +
    # container_height too low
    # solution changes due to init solution in every hypersearch strategy
    # but container_height doesn't,
    # cause no solution is accepted
    prob.container_height = 28

    prob.potential_points_strategy = constants.DEFAULT_POTENTIAL_POINTS_STRATEGY_POOL[0]
    prob.solve()
    solution0 = prob._deepcopy_solution()
    prob.potential_points_strategy = constants.DEFAULT_POTENTIAL_POINTS_STRATEGY_POOL[1]
    prob.solve()
    solution1 = prob._deepcopy_solution()

    prob.hypersearch(_exhaustive=False)
    assert prob.container_height == 28
    # value set at local_search last node
    assert prob._get_container_height() == 28
    assert prob.solution in (solution0, solution1)


def test_container_min_height_not_None():
    strip_pack_width = C3.containers["container_0"]["W"]
    settings = {"max_time_in_seconds": 1}
    prob = HyperPack(items=C3.items_a, strip_pack_width=strip_pack_width, settings=settings)

    # container_height LIMIT + ALL ITEMS IN SOLUTION TEST
    # container_min_height == 50 -> not all the items must be in every solution
    prob._container_min_height = 50
    prob.hypersearch(_exhaustive=False)
    assert prob.container_height == 50
    # value set at local_search last node
    assert prob._get_container_height() == 50
    assert len(C3.items_a) == len(prob.solution[STRIP_PACK_CONT_ID])


def test_doesnt_change_settings():
    from copy import deepcopy

    settings = {"max_time_in_seconds": 10, "workers_num": 1, "figure": {"show": False}}
    containers = {"c_a": {"W": 1, "L": 1}}
    prob = HyperPack(containers=containers, items={"a": {"w": 2, "l": 2}})
    settings = deepcopy(prob.settings)
    prob.hypersearch()
    assert prob.settings == settings


def test_doesnt_change_containers(test_data):
    settings = {"max_time_in_seconds": 1}
    prob = HyperPack(**test_data, settings=settings)
    containers = prob.containers.deepcopy()
    prob.hypersearch()
    assert prob.containers == containers


def test_doesnt_change_items(test_data):
    settings = {"max_time_in_seconds": 1}
    prob = HyperPack(**test_data, settings=settings)
    items = prob.items.deepcopy()
    prob.hypersearch()
    assert prob.items == items
