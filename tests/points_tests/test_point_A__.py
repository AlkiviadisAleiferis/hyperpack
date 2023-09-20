import pytest

from hyperpack import HyperPack


@pytest.mark.parametrize(
    "container,items,points_seq,point_A__,solution_points",
    [
        # 0. A protruding with no touching surface
        (
            (2, 4),
            ((1, 2), (1, 3)),
            ("B", "A__"),
            (1, 3),
            ((0, 0),),
        ),
        # 1. same height items, corners touching
        (
            (2, 4),
            ((1, 2), (1, 2)),
            ("B", "C"),
            (1, 2),
            ((0, 0), (1, 0)),
        ),
    ],
)
def test_point_generation_A__(
    container, items, points_seq, point_A__, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_A__ in prob._current_potential_points["A__"]
    assert point_A__ not in prob._current_potential_points["A"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,point_A__,solution_points",
    [
        # 0. Ay == L
        (
            (2, 4),
            ((2, 2), (2, 2)),
            ("A", "B"),
            (0, 4),
            ((0, 0), (0, 2)),
        ),
        # 1. blocked horizontally from above
        (
            (3, 5),
            ((3, 2), (1, 2), (3, 1), (1, 2)),
            ("A", "B"),
            (1, 4),
            ((0, 0), (0, 2), (0, 4), (1, 2)),
        ),
    ],
)
def test_point_generation_prohibited_A__(
    container, items, points_seq, point_A__, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_A__ not in prob._current_potential_points["A__"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,point_A__,solution_points",
    [  # A GENRATED CASES:
        # 0. A point on left wall, origin item
        (
            (2, 4),
            ((1, 2),),
            ("B", "A__"),
            (0, 2),
            ((0, 0),),
        ),
        # 1. A point on left wall
        (
            (2, 4),
            ((2, 1), (1, 1)),
            ("A", "A__"),
            (0, 2),
            ((0, 0), (0, 1)),
        ),
        # 2. A point on first item's right side
        (
            (2, 4),
            ((1, 2), (1, 1)),
            ("B", "A__"),
            (1, 1),
            ((0, 0), (1, 0)),
        ),
        # 3. A point on second item's right side
        (
            (2, 4),
            ((2, 1), (1, 3), (1, 1)),
            ("B", "A"),
            (1, 2),
            ((0, 0), (0, 1), (1, 1)),
        ),
        # 4. Two items on left
        (
            (2, 5),
            ((2, 1), (1, 1), (1, 3), (1, 3)),
            ("A", "B"),
            (1, 4),
            ((0, 0), (0, 1), (0, 2), (1, 1)),
        ),
        # 5. A point marginally touches bottom right side of another item
        (
            (3, 4),
            ((3, 1), (1, 2), (2, 1), (1, 2)),
            ("A", "B_"),
            (2, 3),
            ((0, 0), (0, 1), (0, 3), (2, 1)),
        ),
        # 6. Two non-continued items on the left
        (
            (3, 6),
            ((3, 1), (1, 1), (2, 1), (2, 2), (1, 1), (1, 3)),
            ("A", "B_"),
            (2, 4),
            ((0, 0), (0, 1), (0, 2), (0, 3), (0, 5), (2, 1)),
        ),
        # 7. item on left touches on A corner
        (
            (6, 8),
            ((2, 7), (3, 1), (1, 5), (1, 7)),
            ("A", "B"),
            (3, 7),
            ((0, 0), (0, 7), (2, 0), (3, 0)),
        ),
    ],
)
def test_point_generation_prohibited_A___due_to_A_gen(
    container, items, points_seq, point_A__, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_A__ not in prob._current_potential_points["A__"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,solution_point",
    [
        (
            (2, 4),
            ((1, 2), (1, 3), (1, 1)),
            ("B", "A__"),
            (1, 3),
        ),
    ],
)
def test_placement_point_A__(container, items, points_seq, solution_point, request):
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
