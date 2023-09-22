import copy
import inspect
import os
from importlib import import_module
from pathlib import Path

from hyperpack import HyperPack

LIB_PATH = Path(os.getcwd())
GEN_SETTINGS = {
    "workers_num": 1,
    "rotate": False,
    "figure": {
        "export": {
            "type": "html",
            "file_name": None,
            "path": None,
        },
        "show": False,
    },  # True/False
}


def rip_off_test_data(point):
    test_module = import_module(f"tests.points_tests.test_point_{point}")
    test_func_success, test_func_failure = (
        eval(f"test_module.test_point_generation_{point}"),
        eval(f"test_module.test_point_generation_prohibited_{point}"),
    )

    code_lines_success = inspect.getsourcelines(test_func_success)[0]
    code_lines_failure = inspect.getsourcelines(test_func_failure)[0]

    success_test_data_lines = []
    prohibited_test_data_lines = []

    for line in code_lines_success[2:]:
        if line.startswith(")"):
            break
        success_test_data_lines.append(line)

    success_data = eval("".join(success_test_data_lines))

    for line in code_lines_failure[2:]:
        if line.startswith(")"):
            break
        prohibited_test_data_lines.append(line)

    failure_data = eval("".join(prohibited_test_data_lines))

    return (success_data, failure_data)


def gen_tests_graphs(point):
    print(f"\tgenerating graphs for point {point}")
    success_tests_data, prohibited_tests_data = rip_off_test_data(point)

    settings = copy.deepcopy(GEN_SETTINGS)
    export_path_success = LIB_PATH / "tests" / "tests_graphs" / f"point_{point}" / "success"
    export_path_prohibited = (
        LIB_PATH / "tests" / "tests_graphs" / f"point_{point}" / "prohibited"
    )
    settings["figure"]["export"]["type"] = "image"
    settings["figure"]["export"]["format"] = "png"
    settings["figure"]["export"]["width"] = 1500
    settings["figure"]["export"]["height"] = 1500

    settings["figure"]["export"]["path"] = str(export_path_success)
    for test in success_tests_data:
        for num, test_data in enumerate(test):
            settings["figure"]["export"]["file_name"] = f"success_{num}"
            container, items, strategy, *_ = test_data
            containers = {"cont-0": {"W": container[0], "L": container[1]}}
            items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
            prob = HyperPack(containers=containers, items=items, settings=settings)
            prob._potential_points_strategy = strategy
            prob.solve(debug=False)
            prob.create_figure()

    settings["figure"]["export"]["path"] = str(export_path_prohibited)
    for test in prohibited_tests_data:
        for num, test_data in enumerate(test):
            settings["figure"]["export"]["file_name"] = f"prohibited_{num}"
            container, items, strategy, *_ = test_data
            containers = {"cont-0": {"W": container[0], "L": container[1]}}
            items = {f"i-{i}": {"w": w, "l": l} for i, (w, l) in enumerate(items)}
            prob = HyperPack(containers=containers, items=items, settings=settings)
            prob._potential_points_strategy = strategy
            prob.solve(debug=False)
            prob.create_figure()
