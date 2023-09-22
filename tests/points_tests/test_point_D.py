import pytest

from hyperpack import HyperPack


@pytest.mark.parametrize(
    "container,items,points_seq,point_D,solution_points",
    [
        # 0. ordinary D. Check if A'' removed
        (
            (4, 8),
            ((2, 2), (2, 3), (2, 4)),
            ("B", "A"),
            (2, 3),
            ((0, 0), (2, 0), (0, 2)),
        ),
    ],
)
def test_point_generation_D(container, items, points_seq, point_D, solution_points, request):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_D in prob._current_potential_points["D"]
    assert point_D not in prob._current_potential_points["B"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)
    assert point_D not in prob._current_potential_points["A__"]


@pytest.mark.parametrize(
    "container,items,points_seq,point_D,solution_points",
    [
        # 0. segment continued not enabling D
        (
            (4, 8),
            ((2, 2), (2, 3), (2, 4), (2, 4)),
            ("B", "A__", "A"),
            (2, 3),
            ((0, 0), (2, 0), (2, 3), (0, 2)),
        ),
        # 1. A point, not C
        (
            (4, 8),
            ((2, 2), (2, 2), (2, 4)),
            ("B", "A"),
            (2, 2),
            ((0, 0), (2, 0), (0, 2)),
        ),
    ],
)
def test_point_generation_prohibited_D(
    container, items, points_seq, point_D, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_D not in prob._current_potential_points["D"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,solution_point",
    [
        (
            (4, 8),
            ((2, 2), (2, 3), (2, 4), (2, 5)),
            ("D", "B", "A"),
            (2, 3),
        ),
    ],
)
def test_placement_point_D(container, items, points_seq, solution_point, request):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    item_index = len(items) - 1
    placement = (
        prob.solution["cont-0"][f"i-{item_index}"][0],
        prob.solution["cont-0"][f"i-{item_index}"][1],
    )
    assert placement == solution_point
