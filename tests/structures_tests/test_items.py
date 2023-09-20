import pytest

from hyperpack import Dimensions, DimensionsError, HyperPack, Items, ItemsError


@pytest.mark.parametrize(
    "items,error_msg,error",
    [
        # missing
        ({}, ItemsError.MISSING, ItemsError),
        (None, ItemsError.MISSING, ItemsError),
        # type
        ("f", ItemsError.TYPE, ItemsError),
        ([], ItemsError.TYPE, ItemsError),
        (1, ItemsError.TYPE, ItemsError),
        (1.2, ItemsError.TYPE, ItemsError),
        # item id type
        ({0: {"w": 10, "l": 10}}, ItemsError.ID_TYPE, ItemsError),
        # items missing
        ({"item_id": {}}, DimensionsError.DIMENSIONS_MISSING, DimensionsError),
        ({"item_id": None}, DimensionsError.DIMENSIONS_MISSING, DimensionsError),
        # type of every item
        ({"item_id": 0}, DimensionsError.DIMENSIONS_TYPE, DimensionsError),
        ({"item_id": "0"}, DimensionsError.DIMENSIONS_TYPE, DimensionsError),
        ({"item_id": 0.0}, DimensionsError.DIMENSIONS_TYPE, DimensionsError),
        # wrong dimension keys
        ({"item_id": {"w": 10}}, DimensionsError.DIMENSIONS_KEYS, DimensionsError),
        ({"item_id": {"l": 10}}, DimensionsError.DIMENSIONS_KEYS, DimensionsError),
        # width/length
        (
            {"item_id": {"w": "10", "l": 10}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"item_id": {"w": 10, "l": "10"}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"item_id": {"w": 0, "l": 10}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"item_id": {"w": 10.1, "l": 0}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"item_id": {"w": 10, "l": 1.1}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"item_id": {"w": 10, "l": 0}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
    ],
)
def test_items_validation_assignment(items, error_msg, error, request):
    caplog = request.getfixturevalue("caplog")
    test_data = request.getfixturevalue("test_data")
    containers = {"cont_id": {"W": 100, "L": 100}}
    with pytest.raises(error) as exc_info:
        prob = HyperPack(containers=test_data["containers"], items=items)
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    # now tests for changing the _items value
    # after instantiation
    prob = HyperPack(**test_data)
    with pytest.raises(error) as exc_info:
        prob.items = items
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


@pytest.mark.parametrize(
    "key_type,key,item,error_msg,error",
    [
        # set items[item_id] = ...
        # missing
        (
            "item_id",
            0,
            {"w": 100, "l": -100},
            ItemsError.ID_TYPE,
            ItemsError,
        ),
        (
            "item_id",
            None,
            {"w": 100, "L": -100},
            ItemsError.ID_TYPE,
            ItemsError,
        ),
        (
            "item_id",
            [1],
            {"w": 100, "l": 100},
            ItemsError.ID_TYPE,
            ItemsError,
        ),
        (
            "item_id",
            "item_id",
            {"l": 100, "w": 100, "f": 1},
            DimensionsError.DIMENSIONS_KEYS,
            DimensionsError,
        ),
        (
            "item_id",
            "item_id",
            {"w": 100},
            DimensionsError.DIMENSIONS_KEYS,
            DimensionsError,
        ),
        (
            "item_id",
            "item_id",
            {"w": 100, "L": 100},
            DimensionsError.DIMENSIONS_KEYS,
            DimensionsError,
        ),
        (
            "item_id",
            "item_id",
            {"l": 100, "W": 100},
            DimensionsError.DIMENSIONS_KEYS,
            DimensionsError,
        ),
        (
            "item_id",
            "item_id",
            {"w": 100, "l": -100},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "item_id",
            "item_id",
            {"w": None, "l": 100},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "item_id",
            "item_id",
            {"w": 100, "l": None},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "item_id",
            "item_id",
            {"w": "100", "l": 100},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "item_id",
            "item_id",
            {"w": 100, "l": "100"},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "item_id",
            "item_id",
            {"w": 100.1, "l": 100},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "item_id",
            "item_id",
            {"w": 100, "l": 100.1},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "item_id",
            "item_id",
            {"w": 100, "l": -100},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "item_id",
            "item_id",
            {"w": -100, "l": 100},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        # dimension setting
        # set items[item_id]["w"] = ...
        ("dimension", "w", 1.1, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "w", -1, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "w", None, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "w", [-1], DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "w", {"a": -1}, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "w", {-1}, DimensionsError.DIMENSION_VALUE, DimensionsError),
        # set items[item_id]["l"] = ...
        ("dimension", "l", 1.1, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "l", -1, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "l", None, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "l", [-1], DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "l", {"a": -1}, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "l", {-1}, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "L", 2, DimensionsError.DIMENSIONS_KEYS, DimensionsError),
    ],
)
def test_items_setitem(key_type, key, item, error_msg, error, request):
    test_data = request.getfixturevalue("test_data")
    containers = test_data["containers"]
    items = {"item_id": {"w": 10, "l": 10}}
    caplog = request.getfixturevalue("caplog")
    prob = HyperPack(containers=containers, items=items)

    with pytest.raises(error) as exc_info:
        if key_type == "item_id":
            prob.items[key] = item
        if key_type == "dimension":
            prob.items["item_id"][key] = item
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    if key_type == "item_id" and not isinstance(key, list):
        with pytest.raises(error) as exc_info:
            prob.items.update({key: item})
        assert str(exc_info.value) == error_msg
        assert error_msg in caplog.text

    if key_type == "dimension" and not isinstance(key, list):
        with pytest.raises(error) as exc_info:
            prob.items["item_id"].update({key: item})
        assert str(exc_info.value) == error_msg
        assert error_msg in caplog.text


def test_items_deletion(caplog):
    items = {"test_id": {"w": 10, "l": 10}}
    containers = {"cont_id": {"W": 100, "L": 100}}
    prob = HyperPack(containers=containers, items=items)

    # deleting the whole items structure error
    with pytest.raises(ItemsError) as exc_info:
        del prob.items
    assert str(exc_info.value) == ItemsError.CANT_DELETE
    assert ItemsError.CANT_DELETE in caplog.text

    # deleting last item error
    error_msg = ItemsError.CANT_DELETE_STRUCTURE
    with pytest.raises(ItemsError) as exc_info:
        del prob.items["test_id"]
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    # safe to delete item
    prob.items["test_id_2"] = {"w": 100, "l": 100}
    prob.solve()
    del prob.items["test_id"]

    # test resetting
    assert prob.solution == {}
    assert prob.obj_val_per_container == {}
    assert prob._containers_num == 1


def test_items_validation_ok():
    containers = {"cont_id": {"W": 1001, "L": 1001}}
    items = {"test_id": {"w": 101, "l": 101}}
    prob = HyperPack(containers=containers, items=items)
    assert prob.containers == containers
    assert prob.items == items
    prob.solve()
    assert prob.solution == {"cont_id": {"test_id": [0, 0, 101, 101]}}

    items = {"test_id": {"w": 101, "l": 101}}
    prob.items = items
    assert prob.containers == containers
    assert prob.items == items
    prob.solve()
    assert prob.solution == {"cont_id": {"test_id": [0, 0, 101, 101]}}

    prob.items["test_id"] = {"w": 102, "l": 101}
    assert prob.containers == containers
    assert prob.items == {"test_id": {"w": 102, "l": 101}}
    prob.solve()
    assert prob.solution == {"cont_id": {"test_id": [0, 0, 102, 101]}}

    prob.items["test_id"]["w"] = 10
    assert prob.containers == containers
    assert prob.items == {"test_id": {"w": 10, "l": 101}}
    prob.solve()
    assert prob.solution == {"cont_id": {"test_id": [0, 0, 10, 101]}}

    prob.items["test_id"]["l"] = 10
    assert prob.containers == containers
    assert prob.items == {"test_id": {"w": 10, "l": 10}}
    prob.solve()
    assert prob.solution == {"cont_id": {"test_id": [0, 0, 10, 10]}}


def test_items_assignment_resets_attributes():
    containers = {"cont_id": {"W": 1001, "L": 1001}}
    items = {"test_id": {"w": 101, "l": 101}}
    prob = HyperPack(containers=containers, items=items)
    prob.solve()
    assert prob.solution == {"cont_id": {"test_id": [0, 0, 101, 101]}}

    items = {"test_id": {"w": 101, "l": 101}}
    prob.items = items
    assert prob.containers == containers
    assert prob.items == items
    assert prob.solution == {}
    assert prob.obj_val_per_container == {}

    prob.solve()
    prob.items["test_id"] = {"w": 102, "l": 101}
    prob.items["test_id_2"] = {"w": 102, "l": 101}
    assert prob.containers == containers
    assert prob.items == {
        "test_id": {"w": 102, "l": 101},
        "test_id_2": {"w": 102, "l": 101},
    }
    assert prob.solution == {}
    assert prob.obj_val_per_container == {}

    prob.solve()
    del prob.items["test_id_2"]
    assert prob.solution == {}
    assert prob.obj_val_per_container == {}
    assert prob.items == {"test_id": {"w": 102, "l": 101}}

    prob.solve()
    prob.items["test_id"]["w"] = 10
    assert prob.containers == containers
    assert prob.items == {"test_id": {"w": 10, "l": 101}}
    assert prob.solution == {}
    assert prob.obj_val_per_container == {}

    prob.solve()
    prob.items["test_id"]["l"] = 10
    assert prob.containers == containers
    assert prob.items == {"test_id": {"w": 10, "l": 10}}
    assert prob.solution == {}
