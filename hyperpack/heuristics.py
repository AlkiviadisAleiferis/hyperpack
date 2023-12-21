import math
import platform
import re
import sys
import time
from collections import deque
from itertools import permutations
from multiprocessing import Array, cpu_count, current_process
from pathlib import Path

from . import constants
from . import mixins
from .abstract import AbstractLocalSearch
from .processes import HyperSearchProcess
from .exceptions import (
    ContainersError,
    MultiProcessError,
    SettingsError,
    DimensionsError,
)
from .loggers import hyperLogger
from .structures import Containers, Items

ITEMS_COLORS = constants.ITEMS_COLORS


class PointGenPack(
    mixins.ContainersUtilsMixin,
    mixins.ItemsUtilsMixin,
    mixins.PointGenSolverMixin,
    mixins.DeepcopyMixin,
    mixins.FigureBuilderMixin,
    mixins.PropertiesMixin,
):
    """
    Base class for initiating and validating the
    attributes of the problem to be solved:
        - Items
        - Containers
        - Settings

    The mixins used are each of them responsible
    for the corresponding functionalities.
    """

    # settings defaults
    MAX_TIME_IN_SECONDS_DEFAULT_VALUE = 60
    WORKERS_NUM_DEFAULT_VALUE = 1
    ROTATION_DEFAULT_VALUE = True
    # strip pack constants
    MAX_W_L_RATIO = 10
    STRIP_PACK_INIT_HEIGHT = 2**100
    STRIP_PACK_CONT_ID = "strip-pack-container"
    # solving constants
    DEFAULT_POTENTIAL_POINTS_STRATEGY = (
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
    INIT_POTENTIAL_POINTS = {
        "O": (0, 0),
        "A": deque(),
        "B": deque(),
        "A_": deque(),
        "B_": deque(),
        "A__": deque(),
        "B__": deque(),
        "C": deque(),
        "D": deque(),
        "E": deque(),
        "F": deque(),
    }
    FIGURE_DEFAULT_FILE_NAME = "PlotlyGraph"
    # settings constraints
    PLOTLY_MIN_VER = ("5", "14", "0")
    PLOTLY_MAX_VER = ("6", "0", "0")
    KALEIDO_MIN_VER = ("0", "2", "1")
    KALEIDO_MAX_VER = ("0", "3", "0")
    FIGURE_FILE_NAME_REGEX = re.compile(r"[a-zA-Z0-9_-]{1,45}$")
    ACCEPTED_IMAGE_EXPORT_FORMATS = ("pdf", "png", "jpeg", "webp", "svg")

    def __init__(
        self, containers=None, items=None, settings=None, *, strip_pack_width=None
    ):
        self._check_strip_pack(strip_pack_width)
        if not self._strip_pack:
            self._containers = Containers(containers, self)
        elif containers is not None:
            raise ContainersError(ContainersError.STRIP_PACK_ONLY)

        self._items = Items(items, self)

        self._max_time_in_seconds = None
        self._workers_num = None
        self._rotation = None
        self._settings = settings or {}
        self._check_plotly_kaleido()
        self.validate_settings()

        # it's the strategy used for the instance. It can be
        # dynamically changed to alter construction heuristic
        self._potential_points_strategy = self.DEFAULT_POTENTIAL_POINTS_STRATEGY
        self._containers_num = len(self._containers)
        self.solution = {}

    def _check_strip_pack(self, strip_pack_width) -> None:
        """
        This method checks ``strip_pack_width`` value and set's initial values for:

            ``_strip_pack``: is the attribute modifying the problem. Used for \
            logic branching in execution. Modifies:

                ``_construct``: Forces the method to accept ``container_height`` \
                as container's height.

                ``local_search``: by lowering the ``container_height`` in every new node.

                ``compare_solution``: Makes comparison check if all items are in solution.

                ``_get_height``: Branches method to return solution height \
                or a minimum.

            ``_container_height``: is the actual container's height used
            in ``_construct``. Is also updated in every new node solution \
            in local_search, where a lower height is proven feasible.

            ``_container_min_height``: is the minimum height that the container \
            can get (not the solution height!).

            ``containers``: with container with preset height for strip packing mode.
        """
        self._container_min_height = None

        if strip_pack_width is None:
            self._strip_pack = False
            self._container_height = None
            self._heights_history = []
            return

        if not isinstance(strip_pack_width, int) or strip_pack_width <= 0:
            raise DimensionsError(DimensionsError.DIMENSION_VALUE)

        self._strip_pack = True
        self._container_height = self.MAX_W_L_RATIO * strip_pack_width
        containers = {
            "strip-pack-container": {
                "W": strip_pack_width,
                "L": self.STRIP_PACK_INIT_HEIGHT,
            }
        }
        self._containers = Containers(containers, self)

    def _check_plotly_kaleido(self) -> None:
        self._plotly_installed = False
        self._plotly_ver_ok = False
        self._kaleido_installed = False
        self._kaleido_ver_ok = False

        try:
            import plotly
        except ImportError:
            pass
        else:
            self._plotly_installed = True
            plotly_ver = tuple([x for x in plotly.__version__.split(".")][:3])
            if plotly_ver >= self.PLOTLY_MIN_VER and plotly_ver < self.PLOTLY_MAX_VER:
                self._plotly_ver_ok = True

        try:
            import kaleido
        except ImportError:
            pass
        else:
            self._kaleido_installed = True
            kaleido_ver = tuple([x for x in kaleido.__version__.split(".")][:3])
            if kaleido_ver >= self.KALEIDO_MIN_VER and kaleido_ver < self.KALEIDO_MAX_VER:
                self._kaleido_ver_ok = True

    def validate_settings(self) -> None:
        """
        Method for validating and applying the settings either
        provided through:
        **A.** instantiation
        **B.** explicit assignment to self.settings
        **C.** calling ``self.validate_settings()``.

        **OPERATION**
            Validates ``settings`` instance attribute data structure and format.

            Applies said settings to correlated private attributes.

        **PARAMETERS**
            ``None``


        **RETURNS**
            `None`
        """

        # % ----------------------------------------------------------------------------
        # SETTINGS VALIDATION
        settings = self._settings
        if not isinstance(settings, dict):
            raise SettingsError(SettingsError.TYPE)

        # % ----------------------------------------------------------------------------
        # IF NO SETTINGS PROVIDED, SET DEFAULT VALUES FOR THESE ATTRIBUTES
        if not settings:
            # if no settings are provided, use DEFAULT values for these attributes
            self._rotation = self.ROTATION_DEFAULT_VALUE
            self._max_time_in_seconds = self.MAX_TIME_IN_SECONDS_DEFAULT_VALUE
            self._workers_num = self.WORKERS_NUM_DEFAULT_VALUE
            return

        # % ----------------------------------------------------------------------------
        # SETTINGS MAX TIME IN SECONDS
        max_time_in_seconds = self._settings.get(
            "max_time_in_seconds", self.MAX_TIME_IN_SECONDS_DEFAULT_VALUE
        )
        if not isinstance(max_time_in_seconds, int):
            raise SettingsError(SettingsError.MAX_TIME_IN_SECONDS_TYPE)

        if max_time_in_seconds < 1:
            raise SettingsError(SettingsError.MAX_TIME_IN_SECONDS_VALUE)
        self._max_time_in_seconds = max_time_in_seconds

        # % ----------------------------------------------------------------------------
        # SETTINGS WORKERS NUM
        workers_num = self._settings.get("workers_num")
        if workers_num is not None:
            try:
                if not workers_num > 0:
                    raise SettingsError(SettingsError.WORKERS_NUM_VALUE)
            except Exception:
                raise SettingsError(SettingsError.WORKERS_NUM_VALUE)
            self._workers_num = workers_num
        else:
            self._workers_num = self.WORKERS_NUM_DEFAULT_VALUE
            workers_num = self.WORKERS_NUM_DEFAULT_VALUE
        if workers_num > cpu_count():
            hyperLogger.warning(SettingsError.WORKERS_NUM_CPU_COUNT_WARNING)

        platform_os = platform.system()
        if (
            workers_num > 1
            and platform_os == "Windows"
            and current_process().name == "MainProcess"
        ):
            hyperLogger.warning(
                "In Windows OS multiprocessing needs 'Entry point protection'"
                "\nwhich means adding if '__name__' == '__main__' before"
                " multiprocessing depending code execution"
            )

        # % ----------------------------------------------------------------------------
        # SETTINGS ROTATION
        rotation = settings.get("rotation")
        if rotation is not None:
            if not isinstance(rotation, bool):
                raise SettingsError(SettingsError.ROTATION_TYPE)
            self._rotation = rotation
        else:
            self._rotation = self.ROTATION_DEFAULT_VALUE

        # % ----------------------------------------------------------------------------
        # FIGURE SETTINGS VALIDATION
        figure_settings = settings.get("figure", {})

        if not isinstance(figure_settings, dict):
            raise SettingsError(SettingsError.FIGURE_KEY_TYPE)

        if figure_settings:
            # plotly library must be installed, and at least 5.14.0 version
            # to enable any figure instantiation/exportation
            if not self._plotly_installed:
                raise SettingsError(SettingsError.PLOTLY_NOT_INSTALLED)

            if not self._plotly_ver_ok:
                raise SettingsError(SettingsError.PLOTLY_VERSION)

            if "export" in figure_settings:
                export = figure_settings.get("export")

                if not isinstance(export, dict):
                    raise SettingsError(SettingsError.FIGURE_EXPORT_VALUE_TYPE)

                export_type = export.get("type")
                if export_type is None:
                    raise SettingsError(SettingsError.FIGURE_EXPORT_TYPE_MISSING)

                if export_type not in ("html", "image"):
                    raise SettingsError(SettingsError.FIGURE_EXPORT_TYPE_VALUE)

                export_path = export.get("path")
                if export_path is None:
                    raise SettingsError(SettingsError.FIGURE_EXPORT_PATH_MISSING)

                if not isinstance(export_path, str):
                    raise SettingsError(SettingsError.FIGURE_EXPORT_PATH_VALUE)

                export_path = Path(export_path)
                if not export_path.exists():
                    raise SettingsError(SettingsError.FIGURE_EXPORT_PATH_NOT_EXISTS)

                if not export_path.is_dir():
                    raise SettingsError(SettingsError.FIGURE_EXPORT_PATH_NOT_DIRECTORY)

                file_format = export.get("format")
                if file_format is None and export_type != "html":
                    raise SettingsError(SettingsError.FIGURE_EXPORT_FORMAT_MISSING)

                if export_type != "html" and not isinstance(file_format, str):
                    raise SettingsError(SettingsError.FIGURE_EXPORT_FORMAT_TYPE)

                accepted_formats = self.ACCEPTED_IMAGE_EXPORT_FORMATS
                if export_type == "image" and file_format not in accepted_formats:
                    raise SettingsError(SettingsError.FIGURE_EXPORT_FORMAT_VALUE)

                file_name = export.get("file_name", None)
                if file_name is None:
                    self._settings["figure"]["export"][
                        "file_name"
                    ] = self.FIGURE_DEFAULT_FILE_NAME
                else:
                    if not isinstance(file_name, str):
                        raise SettingsError(SettingsError.FIGURE_EXPORT_FILE_NAME_TYPE)

                    if not self.FIGURE_FILE_NAME_REGEX.match(file_name):
                        raise SettingsError(SettingsError.FIGURE_EXPORT_FILE_NAME_VALUE)

                if export_type == "image":
                    if not self._kaleido_installed:
                        raise SettingsError(SettingsError.FIGURE_EXPORT_KALEIDO_MISSING)

                    if not self._kaleido_ver_ok:
                        raise SettingsError(SettingsError.FIGURE_EXPORT_KALEIDO_VERSION)

                    export_width = export.get("width")
                    if export_width is not None:
                        if not isinstance(export_width, int) or export_width <= 0:
                            raise SettingsError(SettingsError.FIGURE_EXPORT_WIDTH_VALUE)
                    export_height = export.get("height")
                    if export_height is not None:
                        if not isinstance(export_height, int) or export_height <= 0:
                            raise SettingsError(SettingsError.FIGURE_EXPORT_HEIGHT_VALUE)

            show = figure_settings.get("show", False)
            if "show" in figure_settings and not isinstance(show, bool):
                raise SettingsError(SettingsError.FIGURE_SHOW_VALUE)

    def log_solution(self) -> str:
        """
        Logs the solution.

        If a solution isn't available a proper message is displayed.
        """
        if not getattr(self, "solution", False):
            hyperLogger.warning("No solving operation has been concluded.")
            return

        log = ["\nSolution Log:"]
        percent_items_stored = sum(
            [len(i) for cont_id, i in self.solution.items()]
        ) / len(self._items)
        log.append(f"Percent total items stored : {percent_items_stored*100:.4f}%")

        for cont_id in self._containers:
            L = self._containers._get_height(cont_id)
            W = self._containers[cont_id]["W"]
            log.append(f"Container: {cont_id} {W}x{L}")
            total_items_area = sum(
                [i[2] * i[3] for item_id, i in self.solution[cont_id].items()]
            )
            log.append(f"\t[util%] : {total_items_area*100/(W*L):.4f}%")
            if self._strip_pack:
                solution = self.solution[cont_id]
                # height of items stack in solution
                max_height = max(
                    [solution[item_id][1] + solution[item_id][3] for item_id in solution]
                    or [0]
                )
                log.append(f"\t[max height] : {max_height}")

        items_ids = {_id for cont_id, items in self.solution.items() for _id in items}
        remaining_items = [_id for _id in self._items if _id not in items_ids]
        log.append(f"\nRemaining items : {remaining_items}")
        output_log = "\n".join(log)
        hyperLogger.info(output_log)
        return output_log


class LocalSearch(AbstractLocalSearch):
    def evaluate(self, sequence):
        self.solve(sequence=sequence, debug=False)

    def get_solution(self):
        return (
            self._deepcopy_solution(),
            self._copy_objective_val_per_container(),
        )

    def calculate_obj_value(self):
        """
        Calculates the objective value
        using '`obj_val_per_container`' attribute.

        Returns a float (total utilization).

        In case more than 1 bin is used, last bin's
        utilization is reduced to push first bin's
        maximum utilization.
        """
        containers_obj_vals = tuple(self.obj_val_per_container.values())
        if self._containers_num == 1:
            return sum([u for u in containers_obj_vals])
        else:
            return (
                sum([u for u in containers_obj_vals[:-1]]) + 0.7 * containers_obj_vals[-1]
            )

    def get_init_solution(self):
        self.solve(debug=False)
        # deepcopying solution
        best_solution = self._deepcopy_solution()
        best_obj_val_per_container = self._copy_objective_val_per_container()
        return best_solution, best_obj_val_per_container

    def extra_node_operations(self, **kwargs):
        if self._strip_pack:
            # new height is used for the container
            # for neighbors of new node
            self._containers._set_height()
            self._heights_history.append(self._container_height)

    def node_check(self, new_obj_value, best_obj_value):
        """
        Used in local_search.
        Compares new solution value to best for accepting new node. It's the
        mechanism for propagating towards new accepted better solutions/nodes.

        In bin-packing mode, a simple comparison using solution_operator is made.

        In strip-packing mode, extra conditions will be tested:

            - If ``self._container_min_height`` is ``None``:
                The total of items  must be in solution. \
                If not, solution is rejected.

            - If ``self._container_min_height`` is not ``None``:
                Number of items in solution doesn't affect \
                solution choice.
        """
        better_solution = new_obj_value > best_obj_value

        if not self._strip_pack:
            return better_solution

        if self._container_min_height is None:
            extra_cond = len(self.solution[self.STRIP_PACK_CONT_ID]) == len(self._items)
        else:
            extra_cond = True

        return extra_cond and better_solution

    def local_search(
        self, *, throttle: bool = True, _hypersearch: bool = False, debug: bool = False
    ) -> None:
        """
        Method for deploying a hill-climbing local search operation, using the
        default potential points strategy. Solves against the ``self.items`` and
        the ``self.containers`` attributes.

        **OPERATION**
            Updates ``self.solution`` with the best solution found.

            Updates ``self.obj_val_per_container`` with the best values found.

        **PARAMETERS**
            ``throttle`` affects the total neighbors parsing before accepting that
            no better node can be found. Aims at containing the total execution time
            in big instances of the problem. Corresponds to ~ 72 items instance
            (max 2500 neighbors).

            ``_hypersearch``: Either standalone (False), or part of a
            superset search (used by hypersearch).

            ``debug``: for developing debugging.

        **RETURNS**
            ``None``
        """

        if not _hypersearch:
            start_time = time.time()
        else:
            start_time = self.start_time
            hyperLogger.debug(
                "\t\tCURRENT POTENTIAL POINTS STRATEGY:"
                f" {self._potential_points_strategy}"
            )

        if self._strip_pack:
            self._heights_history = [self._container_height]

        # after local search has ended, restore optimum values
        # retain_solution = (solution, obj_val_per_container)
        retained_solution = super().local_search(
            list(self._items),
            throttle,
            start_time,
            self._max_time_in_seconds,
            debug=debug,
        )
        self.solution, self.obj_val_per_container = retained_solution


class HyperPack(PointGenPack, LocalSearch):
    """
    This class extends ``PointGenPack`` and ``LocalSearch``,
    utilizing their solving functionalities by implementing
    a hypersearch hyper-heuristic.
    """

    # Potential points strategies constant suffix
    STRATEGIES_SUFFIX = ("A__", "B__", "F", "E")
    STRATEGIES_SUFFIX_STRIPACK = ("B__", "A__", "F", "E")
    # max neighbors parsing per node for large instances

    def _check_solution(self, new_obj_val, best_obj_value):
        if new_obj_val > best_obj_value:
            return True
        else:
            return False

    def _get_array_optimum(self, array):
        """
        Using max for maximization else min for minimization.
        """
        if getattr(self, "OPTIMIZATION") == "MAX":
            return max(array)
        else:
            return min(array)

    def get_strategies(self, *, _exhaustive: bool = True) -> tuple:
        """
        Returns the total potential points strategies to be treversed in hypersearch.
        """
        suffixes = (
            self.STRATEGIES_SUFFIX_STRIPACK
            if self._strip_pack
            else self.STRATEGIES_SUFFIX
        )
        if _exhaustive:
            points = set(self.DEFAULT_POTENTIAL_POINTS_STRATEGY)
            points_to_permutate = points.difference(set(suffixes))
            return [
                x + self.STRATEGIES_SUFFIX
                for x in list(
                    permutations(list(points_to_permutate), len(points_to_permutate))
                )
            ]
        else:
            # for testing or customization purposes
            return constants.DEFAULT_POTENTIAL_POINTS_STRATEGY_POOL

    def _single_process_hypersearch(self, strategies: tuple, throttle: bool):
        hyperLogger.debug("Solving with single core")

        # get first solution for comparison
        retain_solution = self.get_init_solution()
        best_obj_value = self.calculate_obj_value()
        optimum_obj_value = self.get_optimum_objective_val()
        best_strategy = self.DEFAULT_POTENTIAL_POINTS_STRATEGY

        for strategy in strategies:
            # set the construction heuristic's potential points strategy
            self._potential_points_strategy = strategy

            self.local_search(throttle=throttle, _hypersearch=True)
            new_obj_val = self.calculate_obj_value()

            if self._check_solution(new_obj_val, best_obj_value):
                best_obj_value = new_obj_val
                retain_solution = self.get_solution()
                best_strategy = [point for point in strategy]
                hyperLogger.debug(f"\tNew best solution: {best_obj_value}\n")

                if self.global_check(new_obj_val, optimum_obj_value):
                    hyperLogger.debug("Terminating due to max objective value obtained")
                    break

            if time.time() - self.start_time > self._max_time_in_seconds:
                hyperLogger.debug("Terminating due to surpassed max time")
                break
        return *retain_solution, best_strategy

    def _multi_process_hypersearch(
        self, strategies: tuple, throttle: bool, _force_raise_error_index
    ):
        strategies_per_process = math.ceil(len(strategies) / self._workers_num)
        strategies_chunks = [
            strategies[i : i + strategies_per_process]
            for i in range(0, len(strategies), strategies_per_process)
        ]

        processes = []
        min_val = 0
        shared_Array = Array("d", [min_val] * len(strategies_chunks))
        container_min_height = getattr(self, "container_min_height", None)
        for i, strategies_chunk in enumerate(strategies_chunks):
            processes.append(
                HyperSearchProcess(
                    index=i,
                    strip_pack=self._strip_pack,
                    containers=self._containers.deepcopy(),
                    items=self._items.deepcopy(),
                    settings=self._settings,
                    strategies_chunk=strategies_chunk,
                    name=f"hypersearch_{i}",
                    start_time=self.start_time,
                    shared_array=shared_Array,
                    throttle=throttle,
                    container_min_height=container_min_height,
                    _force_raise_error_index=_force_raise_error_index,
                )
            )
        for p in processes:
            p.start()
        for p in processes:
            p.join()
        # at this point the processes concluded operation
        shared_list = list(shared_Array)

        # check if all/some processes failed
        if max(shared_list) == -1:
            raise MultiProcessError(MultiProcessError.ALL_PROCESSES_FAILED)
        elif -1 in shared_list:
            hyperLogger.error(
                "Some of the processes raised an exception. Please check logs."
            )

        # get winning process and update instance data
        shared_list_optimum = self._get_array_optimum(shared_list)
        win_process_index = shared_list.index(shared_list_optimum)
        win_process = processes[win_process_index]
        win_metrics = win_process.queue.get()

        best_solution = self._deepcopy_solution(win_metrics[1])
        best_obj_val_per_container = self._copy_objective_val_per_container(
            win_metrics[2]
        )
        if win_metrics[3] is None:
            best_strategy = None
        else:
            best_strategy = [point for point in win_metrics[3]]

        hyperLogger.debug(
            f"\nWinning Process {win_process.name} found max\n"
            f"\tobj_val = {win_metrics[0]}\n\tsequence = {win_metrics[3]}"
        )
        win_process.queue.close()

        # Log rest of the processes
        # UNCOMMENT FOR EXTRA DEBUGGING ON PROCESSES
        for p in processes:
            p.queue.close()

        return (best_solution, best_obj_val_per_container, best_strategy)

    def hypersearch(
        self,
        orientation: str = "wide",
        sorting_by: tuple = ("area", True),
        *,
        throttle: bool = True,
        _exhaustive: bool = True,
        _force_raise_error_index=None,
    ) -> None:
        """
        Method for solving using using a non-learning,
        construction heuristic generation hyper-heuristic,
        utilizing hill climbing local search per generation.

        **OPERATION**
            Solves using ``local_search`` for different
            ``potential_points_strategy`` values.

            - Updates ``self.solution`` with the best solution found.
            - Updates ``self.obj_val_per_container`` with the best values.
            - Updates ``self.best_strategy`` with the best strategy found.

        **PARAMETERS**
            ``orientation`` affects the way items are 'oriented' before
            solving operations start. See :ref:`here<orient_items>` for
            detailed explanation of the method.

            ``sorting_by`` directive for sorting the items attribute before
            solving operations start. See :ref:`here<sort_items>` for
            detailed explanation of the method.

            ``throttle`` boolean **(keyword only)** passed to local search.
            Affects large instances of the problem.

            ``_exhaustive`` boolean **(keyword only)** creates exhaustive search for every
            possible potential points strategy. If false, the search uses predefined
            strategies from ``hyperpack.constants.DEFAULT_POTENTIAL_POINTS_STRATEGY_POOL``
            from ``hyperpack.constants``.

            ``_force_raise_error_index`` **(keyword only)** is used for testing purposes.


        **RETURNS**
            ``None``
        """
        # PRE-SORTING
        # change initial sequence by sorting
        # if spicified None attributes, operations will be skipped
        self.sort_items(sorting_by=sorting_by)
        self.orient_items(orientation=orientation)

        self.start_time = time.time()

        # POTENTIAL POINTS STRATEGIES DETERMINATION
        # exhaustive hypersearch creates all the different potential
        # points strategies, and deployes local search on everyone of them
        # until stopping criteria are met

        strategies = self.get_strategies(_exhaustive=_exhaustive)

        self.solution, self.obj_val_per_container, self.best_strategy = (
            self._single_process_hypersearch(strategies, throttle)
            if self._workers_num == 1
            else self._multi_process_hypersearch(
                strategies, throttle, _force_raise_error_index
            )
        )

        total_time = time.time() - self.start_time
        hyperLogger.debug(f"Execution time : {total_time} [sec]")
