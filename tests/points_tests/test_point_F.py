import pytest

from hyperpack import HyperPack


@pytest.mark.parametrize(
    "container,items,points_seq,point_F,solution_points",
    [
        # 0. projection on Y=0 horizontal
        (
            (3, 5),
            ((1, 1), (1, 1), (1, 1), (2, 1)),
            ("A"),
            (2, 0),
            ((0, 0), (0, 1), (0, 2), (0, 3)),
        ),
        # 1. projection on item below
        (
            (3, 5),
            ((3, 1), (1, 1), (1, 1), (1, 1), (2, 1)),
            ("A"),
            (2, 1),
            ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
        ),
        # 2. projection on item below, double intersegment on landing segment
        (
            (8, 6),
            ((6, 1), (2, 1), (2, 1), (2, 1), (5, 1), (5, 1), (6, 1), (7, 1)),
            ("B", "A"),
            (6, 1),
            ((0, 0), (6, 0), (0, 1), (2, 1), (0, 2), (0, 3)),
        ),
        # 3. projection on item below, double intersegment on landing segment, continuous corner
        (
            (8, 6),
            ((6, 1), (2, 1), (2, 1), (2, 1), (5, 1), (5, 1), (6, 1), (7, 1)),
            ("B", "A"),
            (7, 1),
            ((0, 0), (6, 0), (0, 1), (2, 1), (0, 2), (0, 3)),
        ),
    ],
)
def test_point_generation_F(container, items, points_seq, point_F, solution_points, request):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_F in prob._current_potential_points["F"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,point_F,solution_points",
    [
        # 0. left item obstucting projection
        (
            (5, 5),
            ((2, 1), (2, 1)),
            ("A"),
            (2, 1),
            ((0, 0), (0, 1)),
        ),
        # 1. projection on item below, double intersegment on
        #    non-continuous corner
        (
            (6, 7),
            ((5, 2), (1, 1), (2, 1), (2, 1), (4, 1), (4, 1), (5, 1)),
            ("B", "A"),
            (5, 2),
            ((0, 0), (5, 0), (0, 2), (2, 2), (0, 3), (0, 4), (0, 5)),
        ),
        # 2. projection on item below, double intersegment on
        #    non-continuous corner
        (
            (6, 7),
            ((5, 2), (1, 1), (2, 1), (2, 1), (4, 1), (4, 1), (5, 1)),
            ("B", "A"),
            (5, 1),
            ((0, 0), (5, 0), (0, 2), (2, 2), (0, 3), (0, 4), (0, 5)),
        ),
    ],
)
def test_point_generation_prohibited_F(
    container, items, points_seq, point_F, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_F not in prob._current_potential_points["F"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,solution_point",
    [
        (
            (3, 4),
            ((1, 1), (1, 1), (1, 1), (2, 1), (1, 4)),
            ("F", "A"),
            (2, 0),
        ),
    ],
)
def test_placement_point_F(container, items, points_seq, solution_point, request):
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
