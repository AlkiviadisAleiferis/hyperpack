import re

import pytest

from hyperpack import HyperPack

DEFAULT_POTENTIAL_POINTS_STRATEGY = HyperPack.DEFAULT_POTENTIAL_POINTS_STRATEGY


@pytest.mark.parametrize(
    "containers,items,points_seq,obj_val",
    [
        (((2, 3), (2, 2)), ((2, 3), (1, 1)), ("A", "B"), 1.175),
        (((2, 3),), ((2, 3),), ("A", "B"), 1),
        (((2, 4), (3, 3)), ((2, 2), (3, 3)), ("A", "B"), 1.2),
        (((2, 3), (3, 3), (3, 3)), ((2, 2), (3, 3), (2, 1)), ("A", "B"), 2),
    ],
)
def testcalculate_obj_value(containers, items, points_seq, obj_val):
    containers = {f"cont-{i}": {"W": c[0], "L": c[1]} for i, c in enumerate(containers)}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items)
    prob._potential_points_strategy = points_seq
    prob.solve(debug=True)
    assert obj_val == prob.calculate_obj_value()
    assert len(prob.solution) == len(containers)


def test_deepcopy():
    items = ((2, 3), (12, 3), (12, 14), (1, 1), (4, 6), (7, 9), (1, 2))
    containers = {"cont-0": {"W": 55, "L": 55}}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items)

    items_copy = prob.items.deepcopy()

    assert id(items_copy) != prob.items
    assert items_copy == prob.items
    prob.solve()
    solution_copy = prob._deepcopy_solution()
    assert id(solution_copy) != id(prob.solution)
    assert solution_copy == prob.solution
    obj_val_per_cont_copy = prob._copy_objective_val_per_container()
    assert id(obj_val_per_cont_copy) != id(prob.obj_val_per_container)
    assert obj_val_per_cont_copy == prob.obj_val_per_container
