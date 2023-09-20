import pytest

from hyperpack import HyperPack

from .utils import (
    SOLUTION_LOG_ITEMS_STRATEGY,
    SOLUTION_STRING_CONTAINER,
    SOLUTION_STRING_REMAINING_ITEMS,
)

DEFAULT_POTENTIAL_POINTS_STRATEGY = HyperPack.DEFAULT_POTENTIAL_POINTS_STRATEGY


@pytest.mark.parametrize(
    "containers,items,points_seq,solution_log_vars",
    [
        (
            ((2, 3), (2, 2)),
            ((2, 3), (1, 1)),
            ("A", "B"),
            {
                "prec_items_stored": 100,
                "best_strategy": ("A", "B"),
                "containers_vars": (("cont-0", 2, 3, 100), ("cont-1", 2, 2, 25)),
                "remaining_items": [],
            },
        ),
        (
            ((2, 3),),
            ((3, 3),),
            ("A", "B"),
            {
                "prec_items_stored": 0,
                "best_strategy": ("A", "B"),
                "containers_vars": (("cont-0", 2, 3, 0),),
                "remaining_items": ["i-0"],
            },
        ),
        (
            ((2, 4), (3, 3)),
            ((2, 2), (3, 3), (1, 4)),
            ("A", "B"),
            {
                "prec_items_stored": 66.6667,
                "best_strategy": ("A", "B"),
                "containers_vars": (("cont-0", 2, 4, 50), ("cont-1", 3, 3, 100)),
                "remaining_items": ["i-2"],
            },
        ),
    ],
)
def test_log_solution(containers, items, points_seq, solution_log_vars):
    settings = {"workers_num": 1}
    containers = {f"cont-{i}": {"W": c[0], "L": c[1]} for i, c in enumerate(containers)}
    items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
    prob = HyperPack(containers=containers, items=items, settings=settings)
    prob._potential_points_strategy = points_seq
    prob.solve()

    solution_log = SOLUTION_LOG_ITEMS_STRATEGY.format(
        solution_log_vars["prec_items_stored"],
        solution_log_vars["best_strategy"],
    )
    for container in solution_log_vars["containers_vars"]:
        solution_log += SOLUTION_STRING_CONTAINER.format(*container)
    solution_log += SOLUTION_STRING_REMAINING_ITEMS.format(
        solution_log_vars["remaining_items"]
    )
    solution_log = solution_log.replace("\n", "").replace("\t", "")

    output = prob.log_solution().replace("\n", "").replace("\t", "")

    assert solution_log == output


def test_log_solution_no_solution_found(caplog, test_data):
    prob = HyperPack(**test_data)
    prob.log_solution()
    assert "No solving operation has been concluded." in caplog.text


def test_log_solution_emtpy_container_solution(caplog):
    containers = {"cont_id": {"W": 1, "L": 1}}
    items = {"test_id": {"w": 101, "l": 101}}
    prob = HyperPack(containers=containers, items=items)
    prob.solve()

    solution_log_vars = {
        "prec_items_stored": 0,
        "best_strategy": HyperPack.DEFAULT_POTENTIAL_POINTS_STRATEGY,
        "containers_vars": (("cont_id", 1, 1, 0),),
        "remaining_items": ["test_id"],
    }

    solution_log = SOLUTION_LOG_ITEMS_STRATEGY.format(
        solution_log_vars["prec_items_stored"],
        solution_log_vars["best_strategy"],
    )

    for container in solution_log_vars["containers_vars"]:
        solution_log += SOLUTION_STRING_CONTAINER.format(*container)

    solution_log += SOLUTION_STRING_REMAINING_ITEMS.format(
        solution_log_vars["remaining_items"]
    )

    solution_log = solution_log.replace("\n", "").replace("\t", "")
    output = prob.log_solution().replace("\n", "").replace("\t", "")

    assert solution_log == output
