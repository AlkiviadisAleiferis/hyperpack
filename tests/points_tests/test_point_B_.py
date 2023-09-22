import pytest

from hyperpack import HyperPack


@pytest.mark.parametrize(
    "container,items,points_seq,point_B_,solution_points",
    [
        # 0. projection on Y=0 horizontal
        (
            (3, 5),
            ((1, 1), (2, 1)),
            ("A"),
            (2, 0),
            ((0, 0), (0, 1)),
        ),
        # 1. projection on item below
        (
            (3, 5),
            ((3, 1), (1, 1), (2, 1)),
            ("A"),
            (2, 1),
            ((0, 0), (0, 1), (0, 2)),
        ),
        # 2. projection on item below, double intersegment on landing segment
        (
            (8, 5),
            ((5, 1), (2, 1), (2, 1), (2, 1), (5, 1), (6, 1)),
            ("B", "A"),
            (6, 1),
            ((0, 0), (5, 0), (0, 1), (2, 1), (0, 2), (0, 3)),
        ),
        # 3. projection on item below, double intersegment on landing segment, continuous corner
        (
            (8, 5),
            ((5, 1), (2, 1), (2, 1), (2, 1), (5, 1), (6, 1)),
            ("B", "A"),
            (5, 1),
            ((0, 0), (5, 0), (0, 1), (2, 1), (0, 2), (0, 3)),
        ),
    ],
)
def test_point_generation_B_(container, items, points_seq, point_B_, solution_points, request):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_B_ in prob._current_potential_points["B_"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,point_B_,solution_points",
    [
        # 0. below item obstucting projection seg[1][0] == Bx
        (
            (5, 5),
            ((2, 1), (2, 1)),
            ("A"),
            (2, 1),
            (
                (0, 0),
                (0, 1),
            ),
        ),
        # 1. below item obstucting projection seg[0][0] == Bx
        (
            (5, 5),
            ((1, 2), (1, 1), (3, 2), (2, 1)),
            ("B", "A"),
            (2, 2),
            ((0, 0), (1, 0), (2, 0), (0, 2)),
        ),
        # 2. projection on item below,
        #    non-continuous corner
        (
            (6, 5),
            ((5, 2), (1, 1), (2, 1), (2, 1), (5, 1)),
            ("B", "A"),
            (5, 2),
            ((0, 0), (5, 0), (0, 2), (2, 2), (0, 3)),
        ),
        # 3. projection on item below,
        #    non-continuous corner
        (
            (6, 5),
            ((5, 2), (1, 1), (2, 1), (2, 1), (5, 1)),
            ("B", "A"),
            (5, 1),
            ((0, 0), (5, 0), (0, 2), (2, 2), (0, 3)),
        ),
    ],
)
def test_point_generation_prohibited_B_(
    container, items, points_seq, point_B_, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_B_ not in prob._current_potential_points["B_"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,point_B_,solution_points",
    [
        # B GENERATED CASES
        # 1. Origin item
        (
            (2, 4),
            ((1, 2),),
            ("B",),
            [],
            ((0, 0),),
        ),
        # 2. Second item from origin
        (
            (3, 4),
            ((1, 2), (1, 2)),
            ("B",),
            [],
            ((0, 0), (1, 0)),
        ),
        # 3. On another item
        (
            (3, 4),
            ((3, 1), (1, 1)),
            ("A", "B"),
            [],
            ((0, 0), (0, 1)),
        ),
        # 3. On another item, another on left
        (
            (3, 4),
            ((3, 1), (1, 1), (1, 1)),
            ("B", "A"),
            [],
            ((0, 0), (0, 1), (1, 1)),
        ),
        # 4. On another item, B point between corners
        (
            (2, 4),
            ((1, 1), (1, 1), (1, 1)),
            ("B", "A"),
            [],
            ((0, 0), (1, 0), (0, 1)),
        ),
        # 5. On another item, more than 1 non-continued below
        (
            (4, 4),
            ((1, 2), (1, 1), (2, 2), (3, 1)),
            ("B", "A"),
            [],
            ((0, 0), (1, 0), (2, 0), (0, 2)),
        ),
        # 6. marginnaly touching A corner of below item
        (
            (4, 4),
            ((1, 2), (1, 1), (2, 2), (2, 1)),
            ("B", "A"),
            [],
            ((0, 0), (1, 0), (2, 0), (0, 2)),
        ),
    ],
)
def test_generation_prohibited_point_B__due_to_B_gen(
    container, items, points_seq, point_B_, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_B_ == list(prob._current_potential_points["B_"])
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,solution_point",
    [
        (
            (3, 2),
            ((1, 1), (2, 1), (1, 2)),
            ("A", "B_"),
            (2, 0),
        ),
    ],
)
def test_placement_point_B_(container, items, points_seq, solution_point, request):
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
