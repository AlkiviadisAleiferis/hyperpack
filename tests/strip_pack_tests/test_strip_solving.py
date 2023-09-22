import pytest

from hyperpack import HyperPack, benchmarks

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


def test_solving_container_height():
    strip_pack_width = C3.containers["container_0"]["W"]
    prob = HyperPack(items=C3.items_a, strip_pack_width=strip_pack_width)
    prob.potential_points_strategy = POTENTIAL_POINTS_STRATEGY

    cont_height = prob.container_height
    assert cont_height == prob.MAX_W_L_RATIO * strip_pack_width
    prob.solve()
    assert cont_height == prob.MAX_W_L_RATIO * strip_pack_width

    # reducing container_height restricts solution height
    cont_height = 20
    prob.container_height = cont_height
    prob.solve()
    assert prob._get_container_height(STRIP_PACK_CONT_ID) <= cont_height

    # no item in solution now
    cont_height = 1
    prob.container_height = cont_height
    prob.solve()
    assert prob.solution == {STRIP_PACK_CONT_ID: {}}
    assert prob._get_container_height(STRIP_PACK_CONT_ID) == 0
