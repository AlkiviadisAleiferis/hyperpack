import pytest

from hyperpack import (
    Containers,
    ContainersError,
    Dimensions,
    DimensionsError,
    HyperPack,
)


@pytest.mark.parametrize(
    "containers,error_msg,error",
    [
        # missing
        (None, ContainersError.MISSING, ContainersError),
        ({}, ContainersError.MISSING, ContainersError),
        # type
        ([], ContainersError.TYPE, ContainersError),
        ("[]", ContainersError.TYPE, ContainersError),
        (1, ContainersError.TYPE, ContainersError),
        (1.2, ContainersError.TYPE, ContainersError),
        # container id type
        (
            {0: {"W": 100, "L": 100}},
            ContainersError.ID_TYPE,
            ContainersError,
        ),
        # Dimensions wrong keys
        (
            {"cont_id": {"L": 100}},
            DimensionsError.DIMENSIONS_KEYS,
            DimensionsError,
        ),
        (
            {"cont_id": {"W": 100}},
            DimensionsError.DIMENSIONS_KEYS,
            DimensionsError,
        ),
        (
            {"cont_id": {"w": 100, "L": 100}},
            DimensionsError.DIMENSIONS_KEYS,
            DimensionsError,
        ),
        (
            {"cont_id": {"l": 100, "W": 100}},
            DimensionsError.DIMENSIONS_KEYS,
            DimensionsError,
        ),
        # Dimensions W/L values
        (
            {"cont_id": {"W": None, "L": 100}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"cont_id": {"W": [None], "L": 100}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"cont_id": {"W": None, "L": {"a": 100}}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"cont_id": {"W": 100, "L": None}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"cont_id": {"W": "100", "L": 100}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"cont_id": {"W": 100, "L": "100"}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"cont_id": {"W": 100.1, "L": 100}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"cont_id": {"W": 100, "L": 100.1}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"cont_id": {"W": 100, "L": -100}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            {"cont_id": {"W": -100, "L": 100}},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
    ],
)
def test_containers_validation_assignment(containers, error_msg, error, request):
    items = {"test_id": {"w": 10, "l": 10}}
    caplog = request.getfixturevalue("caplog")
    with pytest.raises(error) as exc_info:
        prob = HyperPack(containers=containers, items=items)
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    # now tests for changing the _containers value
    # after instantiation
    items = {"test_id": {"w": 10, "l": 10}}
    proper_containers = {"cont_id": {"W": 100, "L": 100}}
    prob = HyperPack(containers=proper_containers, items=items)
    caplog = request.getfixturevalue("caplog")
    with pytest.raises(error) as exc_info:
        prob.containers = containers
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


@pytest.mark.parametrize(
    "key_type,key,item,error_msg,error",
    [
        # set containers[container_id] = ...
        # missing
        (
            "container_id",
            0,
            {"W": 100, "L": -100},
            ContainersError.ID_TYPE,
            ContainersError,
        ),
        (
            "container_id",
            None,
            {"W": 100, "L": -100},
            ContainersError.ID_TYPE,
            ContainersError,
        ),
        (
            "container_id",
            [1],
            {"W": 100, "L": -100},
            ContainersError.ID_TYPE,
            ContainersError,
        ),
        (
            "container_id",
            "cont_id",
            {"L": 100},
            DimensionsError.DIMENSIONS_KEYS,
            DimensionsError,
        ),
        (
            "container_id",
            "cont_id",
            {"W": 100},
            DimensionsError.DIMENSIONS_KEYS,
            DimensionsError,
        ),
        (
            "container_id",
            "cont_id",
            {"w": 100, "L": 100},
            DimensionsError.DIMENSIONS_KEYS,
            DimensionsError,
        ),
        (
            "container_id",
            "cont_id",
            {"l": 100, "W": 100},
            DimensionsError.DIMENSIONS_KEYS,
            DimensionsError,
        ),
        (
            "container_id",
            "cont_id",
            {"W": 100.1, "L": 100},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "container_id",
            "cont_id",
            {"W": 100, "L": 100.1},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "container_id",
            "cont_id",
            {"W": 100, "L": -100},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "container_id",
            "cont_id",
            {"W": None, "L": 100},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "container_id",
            "cont_id",
            {"W": 100, "L": None},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "container_id",
            "cont_id",
            {"W": "100", "L": 100},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "container_id",
            "cont_id",
            {"W": 100, "L": "100"},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "container_id",
            "cont_id",
            {"W": 100, "L": -100},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        (
            "container_id",
            "cont_id",
            {"W": -100, "L": 100},
            DimensionsError.DIMENSION_VALUE,
            DimensionsError,
        ),
        # dimension setting
        # set containers[container_id]["W"] = ...
        ("dimension", "W", 1.1, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "W", -1, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "W", None, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "W", [-1], DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "W", {"a": -1}, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "W", {-1}, DimensionsError.DIMENSION_VALUE, DimensionsError),
        # set containers[container_id]["L"] = ...
        ("dimension", "L", 1.1, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "L", -1, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "L", None, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "L", [-1], DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "L", {"a": -1}, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "L", {-1}, DimensionsError.DIMENSION_VALUE, DimensionsError),
        ("dimension", "l", 2, DimensionsError.DIMENSIONS_KEYS, DimensionsError),
    ],
)
def test_containers_validation_setitem(key_type, key, item, error_msg, error, request):
    items = {"test_id": {"w": 10, "l": 10}}
    containers = {"cont_id": {"W": 100, "L": 100}}
    caplog = request.getfixturevalue("caplog")
    prob = HyperPack(containers=containers, items=items)

    with pytest.raises(error) as exc_info:
        if key_type == "container_id":
            prob.containers[key] = item
        if key_type == "dimension":
            prob.containers["cont_id"][key] = item
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    if key_type == "container_id" and not isinstance(key, list):
        with pytest.raises(error) as exc_info:
            prob.containers.update({key: item})
        assert str(exc_info.value) == error_msg
        assert error_msg in caplog.text

    if key_type == "dimension" and not isinstance(key, list):
        with pytest.raises(error) as exc_info:
            prob.containers["cont_id"].update({key: item})
        assert str(exc_info.value) == error_msg
        assert error_msg in caplog.text


def test_containers_deletion(caplog):
    items = {"test_id": {"w": 10, "l": 10}}
    containers = {"cont_id": {"W": 100, "L": 100}}
    prob = HyperPack(containers=containers, items=items)

    # deleting the whole containers structure error
    with pytest.raises(ContainersError) as exc_info:
        del prob.containers
    assert str(exc_info.value) == ContainersError.CANT_DELETE
    assert ContainersError.CANT_DELETE in caplog.text

    # deleting last container error
    error_msg = ContainersError.CANT_DELETE_STRUCTURE
    with pytest.raises(ContainersError) as exc_info:
        del prob.containers["cont_id"]
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    # safe to delete a container
    prob.containers["cont_id_2"] = {"W": 100, "L": 100}
    prob.solve()
    del prob.containers["cont_id"]

    # test resetting
    assert prob.solution == {}
    assert prob.obj_val_per_container == {}
    assert prob._containers_num == 1


def test_containers_validation_ok():
    containers = {"cont_id": {"W": 1001, "L": 1001}}
    items = {"test_id": {"w": 101, "l": 101}}
    prob = HyperPack(containers=containers, items=items)
    assert prob.containers == containers
    assert prob.items == items
    prob.solve()
    assert prob.solution == {"cont_id": {"test_id": [0, 0, 101, 101]}}

    containers = {"cont_id": {"W": 1002, "L": 1002}}
    prob.containers = containers
    assert prob.containers == containers
    assert prob.items == items
    prob.solve()
    assert prob.solution == {"cont_id": {"test_id": [0, 0, 101, 101]}}

    prob.containers["cont_id"] = {"W": 1001, "L": 1001}
    assert prob.containers == {"cont_id": {"W": 1001, "L": 1001}}
    assert prob.items == items
    prob.solve()
    assert prob.solution == {"cont_id": {"test_id": [0, 0, 101, 101]}}

    prob.containers["cont_id"]["W"] = 10002
    assert prob.containers == {"cont_id": {"W": 10002, "L": 1001}}
    assert prob.items == items
    prob.solve()
    assert prob.solution == {"cont_id": {"test_id": [0, 0, 101, 101]}}


def test_containers_assignment_resets_attributes():
    containers = {"cont_id": {"W": 1001, "L": 1001}}
    items = {"test_id": {"w": 101, "l": 101}}
    prob = HyperPack(containers=containers, items=items)
    prob.solve()
    assert prob.solution == {"cont_id": {"test_id": [0, 0, 101, 101]}}

    # now changing the _containers value resets solution
    containers = {"cont_id": {"W": 1002, "L": 1002}}
    prob.containers = containers
    assert prob.containers == containers
    assert prob.items == items
    assert prob.solution == {}
    assert prob.obj_val_per_container == {}
    assert prob._containers_num == 1

    prob.solve()
    prob.containers["cont_id"] = {"W": 1000, "L": 1000}
    prob.containers["cont_id_2"] = {"W": 1000, "L": 1000}
    assert prob.solution == {}
    assert prob.obj_val_per_container == {}
    assert prob._containers_num == 2

    del prob.containers["cont_id_2"]
    assert prob._containers_num == 1

    prob.solve()
    prob.containers["cont_id"]["W"] = 2000
    assert prob.solution == {}
    assert prob.obj_val_per_container == {}

    prob.solve()
    prob.containers["cont_id"]["L"] = 2000
    assert prob.solution == {}
    assert prob.obj_val_per_container == {}


def test_containers__str__():
    containers = {"cont_id": {"W": 1001, "L": 1001}}
    items = {"test_id": {"w": 101, "l": 101}}
    prob = HyperPack(containers=containers, items=items)
    containers_str = """Containers
  - id: cont_id
    width: 1001
    length: 1001""".replace(
        "\n", ""
    )
    __str__output = str(prob.containers).replace("\n", "")
    print(containers_str)
    print(__str__output)
    assert str(__str__output) == containers_str
