import os

import pytest

from hyperpack import HyperPack, SettingsError, DimensionsError, ContainersError

STRIP_PACK_CONT_ID = HyperPack.STRIP_PACK_CONT_ID


# % -------------- strip_pack_width parameter --------------------- %
@pytest.mark.parametrize(
    "strip_pack_width, error, error_msg",
    [
        (0, DimensionsError, DimensionsError.DIMENSION_VALUE),
        (1.1, DimensionsError, DimensionsError.DIMENSION_VALUE),
        ({"a": 1}, DimensionsError, DimensionsError.DIMENSION_VALUE),
        ([0], DimensionsError, DimensionsError.DIMENSION_VALUE),
        ({0}, DimensionsError, DimensionsError.DIMENSION_VALUE),
    ],
)
def test_strip_pack_width_value_error(strip_pack_width, error, error_msg, request):
    test_data = request.getfixturevalue("test_data")
    caplog = request.getfixturevalue("caplog")
    with pytest.raises(error) as exc_info:
        prob = HyperPack(items=test_data["items"], strip_pack_width=strip_pack_width)
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


# % -------------- instantiation attrs --------------------- %
def test_strip_pack_init_ok(test_data):
    strip_pack_width = 10
    prob = HyperPack(items=test_data["items"], strip_pack_width=10)
    assert list(prob.containers.keys()) == [STRIP_PACK_CONT_ID]
    assert prob._strip_pack == True
    assert prob.container_height == prob.MAX_W_L_RATIO * strip_pack_width
    assert prob.container_min_height == None
    assert prob.containers == {
        "strip-pack-container": {"W": 10, "L": prob.STRIP_PACK_INIT_HEIGHT}
    }


def test_NOT_strip_pack_init_ok(test_data):
    prob = HyperPack(**test_data)
    assert prob.containers == test_data["containers"]
    assert prob.items == test_data["items"]
    assert prob.settings == {}
    assert prob._strip_pack == False
    assert prob.container_height is None
    assert prob.container_min_height is None


# % -------------- containers setter --------------------- %
# Can't change containers in strip_pack mode
def test_strip_pack_cant_change_containers(test_data, caplog):
    strip_pack_width = 10
    prob = HyperPack(items=test_data["items"], strip_pack_width=10)
    # when in strip_pack mode, containers cannot be changed
    error_msg = ContainersError.STRIP_PACK_ONLY
    with pytest.raises(ContainersError) as exc_info:
        prob.containers = test_data["containers"]
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    with pytest.raises(ContainersError) as exc_info:
        prob.containers[STRIP_PACK_CONT_ID] = {"W": 10, "L": 10}
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    with pytest.raises(ContainersError) as exc_info:
        prob.containers[STRIP_PACK_CONT_ID]["W"] = 10
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text

    with pytest.raises(ContainersError) as exc_info:
        prob.containers[STRIP_PACK_CONT_ID]["L"] = 10
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


# % -------------- container_height --------------------- %
@pytest.mark.parametrize(
    "height, error, error_msg",
    [
        (0, DimensionsError, DimensionsError.DIMENSION_VALUE),
        (1.1, DimensionsError, DimensionsError.DIMENSION_VALUE),
        ({"a": 1}, DimensionsError, DimensionsError.DIMENSION_VALUE),
        ([0], DimensionsError, DimensionsError.DIMENSION_VALUE),
        ({0}, DimensionsError, DimensionsError.DIMENSION_VALUE),
        (10, ContainersError, ContainersError.STRIP_PACK_MIN_HEIGHT),
    ],
)
def test_container_height_value_error_setter(height, error, error_msg, request):
    test_data = request.getfixturevalue("test_data")
    caplog = request.getfixturevalue("caplog")
    prob = HyperPack(items=test_data["items"], strip_pack_width=100)
    prob._container_min_height = 11
    with pytest.raises(error) as exc_info:
        prob.container_height = height
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


def test_container_height_deleter_error(test_data, caplog):
    prob = HyperPack(items=test_data["items"], strip_pack_width=100)
    with pytest.raises(DimensionsError) as exc_info:
        del prob.container_height
    assert str(exc_info.value) == DimensionsError.CANT_DELETE
    assert DimensionsError.CANT_DELETE in caplog.text


# % -------------- container_min_height --------------------- %
@pytest.mark.parametrize(
    "height, error, error_msg",
    [
        (0, DimensionsError, DimensionsError.DIMENSION_VALUE),
        (1.1, DimensionsError, DimensionsError.DIMENSION_VALUE),
        ({"a": 1}, DimensionsError, DimensionsError.DIMENSION_VALUE),
        ([0], DimensionsError, DimensionsError.DIMENSION_VALUE),
        ({0}, DimensionsError, DimensionsError.DIMENSION_VALUE),
        (12, ContainersError, ContainersError.STRIP_PACK_MIN_HEIGHT),
    ],
)
def test_container_min_height_setter(height, error, error_msg, request):
    test_data = request.getfixturevalue("test_data")
    caplog = request.getfixturevalue("caplog")
    prob = HyperPack(items=test_data["items"], strip_pack_width=100)
    prob._container_height = 11
    with pytest.raises(error) as exc_info:
        prob.container_min_height = height
    assert str(exc_info.value) == error_msg
    assert error_msg in caplog.text


def test_container_min_height_deleter_error(test_data, caplog):
    prob = HyperPack(items=test_data["items"], strip_pack_width=100)
    with pytest.raises(DimensionsError) as exc_info:
        del prob.container_min_height
    assert str(exc_info.value) == DimensionsError.CANT_DELETE
    assert DimensionsError.CANT_DELETE in caplog.text


# % -------------- strip-pack solving attrs unchanged --------------------- %
def test_solving_attrs(test_data, caplog):
    strip_pack_width = 100
    prob = HyperPack(items=test_data["items"], strip_pack_width=strip_pack_width)
    prob.container_height = 11
    prob.container_min_height = 10
    assert prob._strip_pack == True
    assert (
        prob._get_container_height(STRIP_PACK_CONT_ID) == strip_pack_width * prob.MAX_W_L_RATIO
    )

    prob.solve()
    assert prob._strip_pack == True
    assert prob.container_height == 11
    assert prob.container_min_height == 10
    assert prob._get_container_height() == 10

    prob.local_search()
    # no new best solution was found
    assert prob._strip_pack == True
    assert prob.container_height == 11
    assert prob.container_min_height == 10
    assert prob._get_container_height() == 10

    prob.hypersearch()
    assert prob._strip_pack == True
    assert prob.container_height == 11
    assert prob.container_min_height == 10
    assert prob._get_container_height() == 10

    prob.settings = {"workers_num": 2}
    # validate_settings was run
    assert prob._workers_num == 2
    prob.container_height = 11
    prob.container_min_height = 10

    prob.hypersearch()
    assert prob._strip_pack == True
    assert prob.container_height == 11
    assert prob.container_min_height == 10
    assert prob._get_container_height() == 10


# % -------------- NOT strip-pack solving attrs unchanged --------------------- %
def test_NOT_strip_pack_container_solving_attrs(test_data):
    prob = HyperPack(**test_data)
    cont_id = "cont_id"
    L = test_data["containers"][cont_id]["L"]
    assert prob._get_container_height(cont_id) == L

    prob.solve()
    assert prob._strip_pack == False
    assert prob.container_height == None
    assert prob.container_min_height == None
    assert prob._get_container_height(cont_id) == L

    prob.local_search()
    assert prob._strip_pack == False
    assert prob.container_height == None
    assert prob.container_min_height == None
    assert prob._get_container_height(cont_id) == L

    prob.hypersearch()
    assert prob._strip_pack == False
    assert prob.container_height == None
    assert prob.container_min_height == None
    assert prob._get_container_height(cont_id) == L

    prob.settings = {"workers_num": 2}
    # validate_settings was run
    assert prob._workers_num == 2

    prob.hypersearch()
    assert prob._strip_pack == False
    assert prob.container_height == None
    assert prob.container_min_height == None
    assert prob._get_container_height(cont_id) == L
