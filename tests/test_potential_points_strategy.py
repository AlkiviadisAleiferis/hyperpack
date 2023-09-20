import pytest

from hyperpack import HyperPack
from hyperpack.exceptions import PotentialPointsError


@pytest.mark.parametrize(
    "potential_points_strategy,error_msg",
    [
        # wrong type
        ("str", PotentialPointsError.TYPE),
        (["str"], PotentialPointsError.TYPE),
        ({"str": 1}, PotentialPointsError.TYPE),
        (None, PotentialPointsError.TYPE),
        # point wrong type
        ((0, "A"), PotentialPointsError.ELEMENT_TYPE),
        (([0], "A"), PotentialPointsError.ELEMENT_TYPE),
        (({"A": 1}, "A"), PotentialPointsError.ELEMENT_TYPE),
        ((None, "A"), PotentialPointsError.ELEMENT_TYPE),
        # second point wrong type
        (("A", None), PotentialPointsError.ELEMENT_TYPE),
        (("A", [0]), PotentialPointsError.ELEMENT_TYPE),
        (("A", {"A": 1}), PotentialPointsError.ELEMENT_TYPE),
        (("A", (None)), PotentialPointsError.ELEMENT_TYPE),
        # not real point
        (("CC",), PotentialPointsError.ELEMENT_NOT_POINT),
        (("A", "CC"), PotentialPointsError.ELEMENT_NOT_POINT),
        # duplicate point
        (("A", "C", "C"), PotentialPointsError.DUPLICATE_POINTS),
    ],
)
def test_potential_points_setter_error(potential_points_strategy, error_msg, request):
    test_data = request.getfixturevalue("test_data")
    caplog = request.getfixturevalue("caplog")
    prob = HyperPack(**test_data)
    print(HyperPack.DEFAULT_POTENTIAL_POINTS_STRATEGY)
    with pytest.raises(PotentialPointsError) as exc_info:
        prob.potential_points_strategy = potential_points_strategy
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


def test_potential_points_delete_error(test_data, caplog):
    prob = HyperPack(**test_data)

    with pytest.raises(PotentialPointsError) as exc_info:
        del prob.potential_points_strategy
    assert str(exc_info.value) == PotentialPointsError.DELETE
    assert PotentialPointsError.DELETE in caplog.text


def test_potential_points_getter(test_data, caplog):
    prob = HyperPack(**test_data)
    assert prob.potential_points_strategy == HyperPack.DEFAULT_POTENTIAL_POINTS_STRATEGY


def test_potential_points_setter_ok(test_data):
    prob = HyperPack(**test_data)
    prob.potential_points_strategy = ("A", "B")
    assert prob._potential_points_strategy == ("A", "B")
