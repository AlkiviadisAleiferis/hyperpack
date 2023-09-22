import os

import pytest
import time

from hyperpack import HyperPack, benchmarks, HyperSearchProcess, constants

C3 = benchmarks.datasets.hopper_and_turton_2000.C3

STRIP_PACK_CONT_ID = HyperPack.STRIP_PACK_CONT_ID


def test_hypersearch_process_init_attrs():
    strip_pack_width = C3.containers["container_0"]["W"]
    settings = {"max_time_in_seconds": 1}
    prob = HyperPack(items=C3.items_a, strip_pack_width=strip_pack_width, settings=settings)

    hsp = HyperSearchProcess(
        index=0,
        strip_pack=prob._strip_pack,
        containers=prob._containers.deepcopy(),
        items=prob.items.deepcopy(),
        settings=prob._settings,
        strategies_chunk=[],
        name=f"hypersearch_{0}",
        start_time=0,
        shared_array=[],
        throttle=False,
        container_min_height=None,
        _force_raise_error_index=1,
    )

    assert hsp.index == 0
    assert hsp.instance._strip_pack == prob._strip_pack
    assert hsp.instance.containers == prob.containers
    assert hsp.instance.items == prob.items
    assert hsp.instance.start_time == 0
    assert hsp.instance._container_min_height == None
    assert hsp.shared_array == []
    assert hsp.throttle == False
    assert hsp.strategies_chunk == []
    assert hsp.name == f"hypersearch_{0}"


def test_hypersearch_process_strip_pack_solving():
    strip_pack_width = C3.containers["container_0"]["W"]
    settings = {"max_time_in_seconds": 1}
    prob = HyperPack(items=C3.items_a, strip_pack_width=strip_pack_width, settings=settings)

    proc = HyperSearchProcess(
        index=0,
        strip_pack=prob._strip_pack,
        containers=prob._containers.deepcopy(),
        items=prob.items.deepcopy(),
        settings=prob._settings,
        strategies_chunk=[],
        name=f"hypersearch_{0}",
        start_time=0,
        shared_array=[],
        throttle=False,
        container_min_height=None,
        _force_raise_error_index=1,
    )

    proc.instance.potential_points_strategy = constants.DEFAULT_POTENTIAL_POINTS_STRATEGY_POOL[
        0
    ]
    proc.instance.solve()
    solution0 = proc.instance._deepcopy_solution()
    proc.instance.potential_points_strategy = constants.DEFAULT_POTENTIAL_POINTS_STRATEGY_POOL[
        1
    ]
    proc.instance.solve()
    solution1 = proc.instance._deepcopy_solution()

    proc.run()
    assert proc.instance.solution in (solution0, solution1)
    assert prob.items == proc.instance.items
    assert prob.containers == proc.instance.containers
    assert prob.settings == proc.instance.settings


def test_hypersearch_process_solving():
    containers = C3.containers
    items = C3.items_a
    settings = {"max_time_in_seconds": 111}
    prob = HyperPack(containers=containers, items=items, settings=settings)

    proc = HyperSearchProcess(
        index=0,
        strip_pack=prob._strip_pack,
        containers=prob._containers.deepcopy(),
        items=prob.items.deepcopy(),
        settings=prob._settings,
        strategies_chunk=[constants.DEFAULT_POTENTIAL_POINTS_STRATEGY_POOL[0]],
        name=f"hypersearch_{0}",
        start_time=0,  # must be updated before run()
        shared_array=[0, 0],
        throttle=False,
        container_min_height=None,
        _force_raise_error_index=1,
    )

    proc.instance.potential_points_strategy = constants.DEFAULT_POTENTIAL_POINTS_STRATEGY_POOL[
        0
    ]
    proc.instance.local_search()
    solution0 = proc.instance._deepcopy_solution()

    proc.instance.start_time = time.time()
    proc.run()
    assert proc.instance.solution == solution0
    assert prob.items == proc.instance.items
    assert prob.containers == proc.instance.containers
    assert prob.settings == proc.instance.settings
