import pytest

from hyperpack import HyperPack


@pytest.mark.parametrize(
    "container,items,points_seq,point_B__,solution_points",
    [
        # 0. B on top of item. non-continued corner
        (
            (2, 4),
            ((1, 1), (1, 1)),
            ("A",),
            (1, 1),
            ((0, 0), (0, 1)),
        ),
        # 1. B protruding
        (
            (3, 4),
            ((1, 1), (2, 1)),
            ("A",),
            (2, 1),
            ((0, 0), (0, 1)),
        ),
    ],
)
def test_point_generation_B__(
    container, items, points_seq, point_B__, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_B__ in prob._current_potential_points["B__"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,point_B__,solution_points",
    [
        # 0. Bx == L
        (
            (2, 4),
            ((1, 2), (1, 2)),
            ("B",),
            (2, 0),
            ((0, 0), (1, 0)),
        ),
        # 1. B blocked by vertical
        (
            (3, 4),
            ((2, 1), (1, 3), (2, 1)),
            ("B", "A"),
            (2, 1),
            ((0, 0), (2, 0), (0, 1)),
        ),
    ],
)
def test_point_generation_prohibited_B__(
    container, items, points_seq, point_B__, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_B__ not in prob._current_potential_points["B__"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,point_B__,solution_points",
    [
        # B GENERATED CASES
        # 0. Origin item
        (
            (2, 4),
            ((1, 2),),
            ("B",),
            (1, 0),
            ((0, 0),),
        ),
        # 1. Second item from origin
        (
            (3, 4),
            ((1, 2), (1, 2)),
            ("B",),
            (2, 0),
            ((0, 0), (1, 0)),
        ),
        # 2. On another item
        (
            (3, 4),
            ((3, 1), (1, 1)),
            ("A", "B"),
            (1, 1),
            ((0, 0), (0, 1)),
        ),
        # 3. On another item, B point between corners
        (
            (2, 4),
            ((1, 1), (1, 1), (1, 1)),
            ("B", "A"),
            (1, 1),
            ((0, 0), (1, 0), (0, 1)),
        ),
        # 4. On another item, more than 1 non-continued below
        (
            (4, 4),
            ((1, 2), (1, 1), (2, 2), (3, 1)),
            ("B", "A"),
            (3, 2),
            ((0, 0), (1, 0), (2, 0), (0, 2)),
        ),
        # 5. marginnaly touching A corner of below item
        (
            (4, 4),
            ((1, 2), (1, 1), (2, 2), (2, 1)),
            ("B", "A"),
            (2, 2),
            ((0, 0), (1, 0), (2, 0), (0, 2)),
        ),
    ],
)
def test_point_generation_prohibited_B___due_to_B_gen(
    container, items, points_seq, point_B__, solution_points, request
):
    settings = request.getfixturevalue("point_gen_settings")
    containers = {"cont-0": {"W": container[0], "L": container[1]}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert point_B__ not in prob._current_potential_points["B__"]
    for num, point in enumerate(solution_points):
        assert prob.solution["cont-0"][f"i-{num}"][0:2] == list(point)


@pytest.mark.parametrize(
    "container,items,points_seq,solution_point",
    [
        (
            (2, 2),
            ((1, 1), (1, 1), (1, 1)),
            ("A", "B__"),
            (1, 1),
        ),
    ],
)
def test_placement_point_B__(container, items, points_seq, solution_point, request):
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
