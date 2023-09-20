import pytest

from hyperpack import HyperPack, HyperSearchProcess
from hyperpack.benchmarks.datasets.hopper_and_turton_2000.C3 import containers, items_a

DEFAULT_POTENTIAL_POINTS_STRATEGY = HyperPack.DEFAULT_POTENTIAL_POINTS_STRATEGY


def test_hyper_search_process():
    items = ((1, 1), (2, 2), (3, 3))
    containers = {"cont-0": {"W": 22, "L": 22}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items)
    settings = {}

    process = HyperSearchProcess(
        index=0,
        containers=prob.containers.deepcopy(),
        items=prob.items.deepcopy(),
        settings=prob._settings,
        strategies_chunk=(),
        name=f"hypersearch_0",
        start_time=0,
        shared_array=None,
    )
    assert process.hyper_instance.__class__ == HyperPack
    assert process.hyper_instance.containers == containers
    assert process.hyper_instance.items == items
    assert process.hyper_instance.settings == settings
    assert process.hyper_instance.start_time == 0
    assert process.strategies_chunk == ()
    assert process.shared_array == None

    prob.sort_items()
    prob.orient_items()
    process = HyperSearchProcess(
        index=0,
        containers=prob.containers.deepcopy(),
        items=prob.items.deepcopy(),
        settings=prob._settings,
        strategies_chunk=(),
        name=f"hypersearch_0",
        start_time=0,
        shared_array=None,
    )
    assert process.hyper_instance.items == items
