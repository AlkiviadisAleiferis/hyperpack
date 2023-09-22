"""
Development tool for various operations.

arguments:
    --create-tests-graphs:
        Creates all the potential points tests graphs automatically
        by inspecting the pytests' parametrize parameters for every test.

    --profile:
        Profile the local search for the corresponding benchmarks.
        Available choices:
            C1, C2, ..., C7

    -p , --problem: the specific items set for profiling. Defaults to 'a'.
        Available choices:
            a, b, c
"""
import cProfile
import os
import pstats
from argparse import ArgumentParser
from multiprocessing import Process, Queue
from pathlib import Path

from hyperpack.benchmarks.datasets import hopper_and_turton_2000
from hyperpack.heuristics import HyperPack
from tests.tests_graphs.generate_graphs import gen_tests_graphs

parser = ArgumentParser(
    prog="Auxiliary commands for development process.",
    description="A series of different commands helping the development process.",
)

parser.add_argument(
    "--create-tests-graphs",
    help="Creates tests graphs for all the potential points tests",
    action="store_true",
    dest="create_tests_graphs",
    default=False,
)

parser.add_argument(
    "--profile",
    help="Profiling for certain dataset form hyperpack.benchmarks.dataset",
    action="store",
    dest="profile",
    choices=["C" + str(i) for i in range(1, 8)],
)

parser.add_argument(
    "-p",
    "--problem",
    help="Choose specific items set from the dataset",
    action="store",
    dest="problem",
    choices=["a", "b", "c"],
    default="a",
)

args = parser.parse_args()


class DirectoryNotFoundError(Exception):
    pass


def generate_tests_graphs():
    print("Generating tests graphs at location tests/tests_graphs/")
    POINTS_TO_GRAPH = ("A", "A_", "A__", "B", "B_", "B__", "C", "D", "E", "F")
    graphs_path = Path(os.getcwd()) / "tests/tests_graphs"
    if not graphs_path.exists():
        raise DirectoryNotFoundError(
            "'tests/tests_graphs' path not found in library's directory"
        )

    for point in POINTS_TO_GRAPH:
        p0 = graphs_path / f"point_{point}"
        if not p0.exists():
            p0.mkdir()

        p1 = p0 / "success"
        if not p1.exists():
            p1.mkdir()

        p2 = p0 / "prohibited"
        if not p2.exists():
            p2.mkdir()

        gen_tests_graphs(point)

    print("tests graphs generation complete")


# Abstract Process subclass for future development
class AbstractProcess(Process):
    def __init__(self, param):
        super().__init__()
        self.param = param
        self.queue = Queue()

    def run(self):
        pass


if __name__ == "__main__":
    if args.create_tests_graphs:
        generate_tests_graphs()

    elif args.profile:
        problem = args.problem

        C = getattr(hopper_and_turton_2000, args.profile)
        containers = {}
        containers.update({"container_0": C.containers["container_0"]})
        items = C.items_a
        settings = {
            "rotate": True,  # True/False
            "show": True,  # True/False
        }

        a = HyperPack(containers=containers, items=items, settings=settings)
        print("Number of items : ", len(a.items))
        print(a.containers)

        pr = cProfile.Profile()
        pr.enable()

        a.local_search(debug=True)

        pr.disable()
        ps = pstats.Stats(pr)
        ps.strip_dirs().sort_stats("cumulative")
        ps.print_stats()
        ps.dump_stats("profiler.prof")

    else:
        print(__doc__)
