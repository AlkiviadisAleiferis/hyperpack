from hyperpack import HyperPack
from hyperpack.mixins import PointGenerationMixin
import logging
import random
logging.basicConfig(level=logging.DEBUG)

# W = random.randint(50, 70)
# L = random.randint(50, 70)
# H = random.randint(50, 70)

W = 50
L = 50
H = 50

items = {
    # "item1": {
    #     "w": 10,
    #     "l": 15,
    #     "h": 10
    # },
    # "item2": {
    #     "w": 5,
    #     "l": 8,
    #     "h": 10
    # },
    # "item3": {
    #     "w": 20,
    #     "l": 10,
    #     "h": 6
    # },
    # "item4": {
    #     "w": 8,
    #     "l": 10,
    #     "h": 15
    # },
    # "item5": {
    #     "w": 10,
    #     "l": 10,
    #     "h": 12
    # },
    # "item6": {
    #     "w": 20,
    #     "l": 10,
    #     "h": 10
    # },
    # "item7": {
    #     "w": 20,
    #     "l": 12,
    #     "h": 10
    # },
}
for i in range(1, 40):
    items.update(
        [(f"item{i}", {
            "w": random.randint(1, 20),
            "l": random.randint(15, 30),
            "h": random.randint(10, 30)
        })]
    )
containers = {
    "container1": {
        'W': W,
        'L': L,
        'H': H
    },
    "container2": {
        'W': 40,
        'L': 50,
        'H': 50
    }
}

if __name__ == "__main__":
    problem = HyperPack(containers=containers, items=items)
    problem.hypersearch()
    print(problem.log_solution())
    problem.create_figure(show=True)