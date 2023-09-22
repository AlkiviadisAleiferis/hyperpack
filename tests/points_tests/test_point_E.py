import pytest

from hyperpack import HyperPack


@pytest.mark.parametrize(
    "container,items,points_seq,point_E,solution_points",
    [
        # 0. projection on left wall
        (
            (5, 5),
            ((1, 2), (1, 2), (1, 2), (1, 3)),
            ("B"),
            (0, 3),
            ((0, 0), (1, 0), (2, 0), (3, 0)),
        ),
        # 1. E point on item on left
        (
            (5, 5),
            ((1, 4), (1, 2), (1, 1), (1, 1), (1, 3)),
            ("B"),
            (1, 3),
            ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0)),
        ),
        # 2. E point on item on left, 1 double intersegment, continuous landing corner
        (
            (5, 7),
            ((1, 6), (1, 1), (1, 4), (1, 4), (1, 4), (1, 1), (1, 6)),
            ("A", "B"),
            (1, 6),
            ((0, 0), (0, 6), (1, 0), (2, 0), (3, 0), (1, 4), (4, 0)),
        ),
        # 3. E point on item on left, double intersegment on landing
        #    and continuous landing corner
        (
            (5, 7),
            ((1, 3), (1, 3), (1, 1), (1, 4), (1, 4), (1, 4), (1, 1), (1, 6)),
            ("A", "B"),
            (1, 6),
            ((0, 0), (0, 3), (0, 6), (1, 0), (2, 0), (3, 0), (1, 4), (4, 0)),
        ),
        # 4. A' point on item on left, double intersegment on landing
        #    and corner protruding to the right, non continuous
        (
            (6, 7),
            ((1, 3), (1, 3), (2, 1), (1, 4), (1, 4), (1, 4), (1, 4), (1, 1), (1, 6)),
            ("A", "B"),
            (2, 6),
            ((0, 0), (0, 3), (0, 6), (1, 0), (2, 0), (3, 0), (4, 0), (1, 4), (5, 0)),
        ),
        # 5. A' point on item on left, standalone landing corner intersegment
        (
            (7, 7),
            ((1, 3), (1, 3), (3, 1), (1, 4), (2, 4), (1, 4), (1, 4), (1, 1), (1, 6)),
            ("A", "B"),
            (3, 6),
            ((0, 0), (0, 3), (0, 6), (1, 0), (2, 0), (4, 0), (5, 0), (1, 4), (6, 0)),
        ),
    ],
)
def test_point_generation_E(container, items, points_seq, point_E, solution_points, request):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_E in prob._current_potential_points["E"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,point_E,solution_points",
    [
        # 0. left item obstucting projection
        (
            (5, 5),
            ((1, 2), (1, 2)),
            ("B"),
            (1, 2),
            ((0, 0), (1, 0)),
        ),
        # 1. left item obstucting projection, many intersegments + double
        (
            (6, 8),
            ((1, 7), (1, 6), (1, 3), (1, 3), (1, 5), (1, 7)),
            ("A", "B"),
            (1, 7),
            ((0, 0), (1, 0), (2, 0), (2, 3), (3, 0), (4, 0)),
        ),
    ],
)
def test_point_generation_prohibited_E(
    container, items, points_seq, point_E, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_E not in prob._current_potential_points["E"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,solution_point",
    [
        (
            (4, 4),
            ((1, 2), (1, 2), (1, 2), (1, 3), (4, 1)),
            ("E", "B"),
            (0, 3),
        ),
    ],
)
def test_placement_point_E(container, items, points_seq, solution_point, request):
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
