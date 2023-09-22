import pytest

from hyperpack import HyperPack


@pytest.mark.parametrize(
    "container,items,points_seq,point_C,solution_points",
    [
        # 0. ordinary C. Check if B'' removed
        (
            (6, 8),
            ((2, 7), (3, 1), (2, 7)),
            ("A", "B"),
            (3, 7),
            ((0, 0), (0, 7), (2, 0)),
        ),
    ],
)
def test_point_generation_C(container, items, points_seq, point_C, solution_points, request):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_C in prob._current_potential_points["C"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)
    assert point_C not in prob._current_potential_points["B__"]


@pytest.mark.parametrize(
    "container,items,points_seq,point_C,solution_points",
    [
        # 0. segment continued not enabling C
        (
            (6, 8),
            ((2, 7), (3, 1), (3, 1), (2, 7)),
            ("A", "B__", "B"),
            (3, 7),
            ((0, 0), (0, 7), (3, 7), (2, 0)),
        ),
    ],
)
def test_point_generation_prohibited_C(
    container, items, points_seq, point_C, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_C not in prob._current_potential_points["C"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,solution_point",
    [
        (
            (4, 8),
            ((2, 7), (3, 1), (2, 7), (1, 1)),
            ("C", "A", "B"),
            (3, 7),
        ),
    ],
)
def test_placement_point_C(container, items, points_seq, solution_point, request):
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
