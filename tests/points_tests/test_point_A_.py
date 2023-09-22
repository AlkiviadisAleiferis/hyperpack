import pytest

from hyperpack import HyperPack


@pytest.mark.parametrize(
    "container,items,points_seq,point_A_,solution_points",
    [
        # 0. projection on left wall
        (
            (5, 5),
            ((1, 2), (1, 3)),
            ("B"),
            (0, 3),
            ((0, 0), (1, 0)),
        ),
        # 1. A' point on item on left
        (
            (5, 5),
            ((1, 4), (1, 2), (1, 1), (1, 3)),
            ("B"),
            (1, 3),
            ((0, 0), (1, 0), (2, 0), (3, 0)),
        ),
        # 2. A' point on item on left, 1 double intersegment, continuous landing corner
        (
            (5, 7),
            ((1, 6), (1, 1), (1, 4), (1, 4), (1, 1), (1, 6)),
            ("A", "B"),
            (1, 6),
            ((0, 0), (0, 6), (1, 0), (2, 0), (1, 4), (3, 0)),
        ),
        # 3. A' point on item on left, double intersegment on landing
        #    and continuous landing corner
        (
            (5, 7),
            ((1, 3), (1, 3), (1, 1), (1, 4), (1, 4), (1, 1), (1, 6)),
            ("A", "B"),
            (1, 6),
            ((0, 0), (0, 3), (0, 6), (1, 0), (2, 0), (1, 4), (3, 0)),
        ),
        # 4. A' point on item on left, double intersegment on landing
        #    and corner protruding to the right, non continuous
        (
            (5, 7),
            ((1, 3), (1, 3), (2, 1), (1, 4), (1, 4), (1, 1), (1, 6)),
            ("A", "B"),
            (2, 6),
            ((0, 0), (0, 3), (0, 6), (1, 0), (2, 0), (1, 4), (3, 0)),
        ),
        # 5. A' point on item on left, standalone landing corner intersegment
        (
            (5, 7),
            ((1, 3), (1, 3), (3, 1), (1, 4), (2, 4), (1, 1), (1, 6)),
            ("A", "B"),
            (3, 6),
            ((0, 0), (0, 3), (0, 6), (1, 0), (2, 0), (1, 4), (4, 0)),
        ),
    ],
)
def test_point_generation_A_(container, items, points_seq, point_A_, solution_points, request):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_A_ in prob._current_potential_points["A_"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,point_A_,solution_points",
    [
        # 0. left item obstucting projection vertical seg_Xo[1][1] == Ay
        (
            (5, 5),
            ((1, 2), (1, 2)),
            ("B"),
            (1, 2),
            ((0, 0), (1, 0)),
        ),
        # 1. non-continued corner projection, many intersegments + double
        (
            (6, 8),
            ((1, 7), (1, 6), (1, 3), (1, 3), (1, 5), (1, 7)),
            ("A", "B"),
            (1, 7),
            ((0, 0), (1, 0), (2, 0), (2, 3), (3, 0), (4, 0)),
        ),
        # 2. must be E point (too many intersegments)
        (
            (6, 8),
            ((1, 8), (1, 6), (1, 3), (1, 3), (1, 5), (1, 7)),
            ("A", "B"),
            (1, 7),
            ((0, 0), (1, 0), (2, 0), (2, 3), (3, 0), (4, 0)),
        ),
        # 3. non-continued corner projection 2
        (
            (6, 8),
            ((2, 7), (1, 1), (1, 5), (1, 7)),
            ("A", "B"),
            (2, 7),
            ((0, 0), (0, 7), (2, 0), (3, 0)),
        ),
        # 4. item on left touches on A corner
        (
            (6, 8),
            ((2, 7), (3, 1), (1, 5), (1, 7)),
            ("A", "B"),
            (3, 7),
            ((0, 0), (0, 7), (2, 0), (3, 0)),
        ),
    ],
)
def test_point_generation_prohibited_A_(
    container, items, points_seq, point_A_, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_A_ not in prob._current_potential_points["A_"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,point_A_,solution_points",
    [
        # 0. A point on left wall, origin item
        (
            (2, 4),
            ((1, 2),),
            ("B", "A__"),
            [],
            ((0, 0),),
        ),
        # 1. A point on left wall
        (
            (2, 4),
            ((2, 1), (1, 1)),
            ("A", "A__"),
            [],
            ((0, 0), (0, 1)),
        ),
        # 2. A point on first item's right side
        (
            (2, 4),
            ((1, 2), (1, 1)),
            ("B", "A__"),
            [],
            ((0, 0), (1, 0)),
        ),
        # 3. A point on second item's right side
        (
            (2, 4),
            ((2, 1), (1, 3), (1, 1)),
            ("B", "A"),
            [],
            ((0, 0), (0, 1), (1, 1)),
        ),
        # 4. Two items on left
        (
            (2, 5),
            ((2, 1), (1, 1), (1, 3), (1, 3)),
            ("A", "B"),
            [],
            ((0, 0), (0, 1), (0, 2), (1, 1)),
        ),
        # 5. A point marginally touches bottom right side of another item
        (
            (3, 4),
            ((3, 1), (1, 2), (2, 1), (1, 2)),
            ("A", "B_"),
            [],
            ((0, 0), (0, 1), (0, 3), (2, 1)),
        ),
        # 6. Two non-continued items on the left
        (
            (3, 6),
            ((3, 1), (1, 1), (2, 1), (2, 2), (1, 1), (1, 3)),
            ("A", "B_"),
            [],
            ((0, 0), (0, 1), (0, 2), (0, 3), (0, 5), (2, 1)),
        ),
        # 7. item on left touches on A corner
        (
            (6, 8),
            ((2, 7), (3, 1), (1, 5), (1, 7)),
            ("A", "B"),
            [],
            ((0, 0), (0, 7), (2, 0), (3, 0)),
        ),
    ],
)
def test_point_generation_prohibited_A__due_to_A_gen(
    container, items, points_seq, point_A_, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_A_ == list(prob._current_potential_points["A_"])
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,solution_point",
    [
        (
            (2, 5),
            ((1, 2), (1, 3), (2, 1)),
            ("B", "A_"),
            (0, 3),
        ),
    ],
)
def test_placement_point_A_(container, items, points_seq, solution_point, request):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob.potential_points_strategy = points_seq
    prob.solve(debug=True)
    item_index = len(items) - 1
    placement = (
        prob.solution["cont-0"][f"i-{item_index}"][0],
        prob.solution["cont-0"][f"i-{item_index}"][1],
    )
    assert placement == solution_point
