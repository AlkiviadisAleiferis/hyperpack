import pytest

from hyperpack import (
    Containers,
    Items,
    ContainersError,
    Dimensions,
    DimensionsError,
    HyperPack,
)


def test_Dimensions_reference_structure_ok(test_data):
    items = Items(test_data["items"])
    d = Dimensions({"w": 1, "l": 1}, reference_structure=items)
    assert d.proper_keys == {"w", "l"}

    containers = Containers(test_data["containers"])
    d = Dimensions({"W": 1, "L": 1}, reference_structure=containers)
    assert d.proper_keys == {"W", "L"}


def test_Dimensions_wrong_reference_structure_error(caplog):
    error_msg = DimensionsError.DIMENSIONS_REFERENCE_OBJECT
    with pytest.raises(DimensionsError) as exc_info:
        d = Dimensions({"w": 1, "l": 1}, reference_structure="wrong")
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


def test_Dimensions_reference_structure_container_error(test_data, caplog):
    with pytest.raises(DimensionsError) as exc_info:
        containers = Containers(test_data["containers"])
        d = Dimensions({"w": 1, "l": 1}, reference_structure=containers)
    assert str(exc_info.value) == DimensionsError.DIMENSIONS_KEYS
    assert DimensionsError.DIMENSIONS_KEYS in caplog.text


def test_Dimensions_reference_structure_item_error(test_data, caplog):
    with pytest.raises(DimensionsError) as exc_info:
        items = Items(test_data["items"])
        d = Dimensions({"W": 1, "L": 1}, reference_structure=items)
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
