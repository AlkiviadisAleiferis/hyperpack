import pytest

from hyperpack import (
    Containers,
    ContainersError,
    Dimensions,
    DimensionsError,
    HyperPack,
)


def test_Dimensions_reference_structure_ok():
    d = Dimensions({"w": 1, "l": 1}, reference_structure="item")
    assert d.proper_keys == {"w", "l"}

    d = Dimensions({"W": 1, "L": 1}, reference_structure="container")
    assert d.proper_keys == {"W", "L"}


def test_Dimensions_wrong_reference_structure_error(caplog):
    error_msg = DimensionsError.DIMENSIONS_REFERENCE_OBJECT
    with pytest.raises(DimensionsError) as exc_info:
        d = Dimensions({"w": 1, "l": 1}, reference_structure="wrong")
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


def test_Dimensions_reference_structure_container_error(caplog):
    with pytest.raises(DimensionsError) as exc_info:
        d = Dimensions({"w": 1, "l": 1}, reference_structure="container")
    assert str(exc_info.value) == DimensionsError.DIMENSIONS_KEYS
    assert DimensionsError.DIMENSIONS_KEYS in caplog.text


def test_Dimensions_reference_structure_item_error(caplog):
    with pytest.raises(DimensionsError) as exc_info:
        d = Dimensions({"W": 1, "L": 1}, reference_structure="item")
    assert str(exc_info.value) == DimensionsError.DIMENSIONS_KEYS
    assert DimensionsError.DIMENSIONS_KEYS in caplog.text


def test_containers_cant_delete_error(caplog):
    items = {"test_id": {"w": 10, "l": 10}}
    containers = {"cont_id": {"W": 100, "L": 100}}
    prob = HyperPack(containers=containers, items=items)

    with pytest.raises(DimensionsError) as exc_info:
        del prob.containers["cont_id"]["W"]
    assert str(exc_info.value) == DimensionsError.CANT_DELETE
    assert DimensionsError.CANT_DELETE in caplog.text

    with pytest.raises(DimensionsError) as exc_info:
        del prob.containers["cont_id"]["L"]
    assert str(exc_info.value) == DimensionsError.CANT_DELETE
    assert DimensionsError.CANT_DELETE in caplog.text

    error_msg = DimensionsError.CANT_DELETE
    with pytest.raises(DimensionsError) as exc_info:
        del prob.items["test_id"]["w"]
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    error_msg = DimensionsError.CANT_DELETE
    with pytest.raises(DimensionsError) as exc_info:
        del prob.items["test_id"]["l"]
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text
