from hyperpack.mixins import PointGenerationMixin

items = {
    "item1": {
        'w': 10,
        'l': 20,
        'h': 30,
    },
    "item2": {
        'w': 15,
        'l': 25,
        'h': 15,
    },
    "item3": {
        'w': 5,
        'l': 5,
        'h': 5,
    },
}
container = {
    'W': 15,
    'L': 20,
    'H': 55
}

point_gen = PointGenerationMixin()
point_gen._potential_points_strategy = (
        "A",
        "B",
        "C",
        "D",
        "A_",  # A' point
        "B_",  # B' point
        "B__",  # B" point
        "A__",  # A" point
        "E",
        "F",
    )
point_gen._rotation = True
leftover, score, sol = point_gen._construct_solution(container=container, items=items)

print(sol, score)