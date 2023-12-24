import math
import platform
import sys
import time
from itertools import permutations
from multiprocessing import Array, cpu_count, current_process

from . import constants
from . import mixins
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


class BasePackingProblem(mixins.StructuresPropertiesMixin):
    """
    Base class for initializing/managing
    the base packing problem attributes.
    """

    # strip pack constants
    MAX_W_L_RATIO = 10
    STRIP_PACK_INIT_HEIGHT = 2**100
    STRIP_PACK_CONT_ID = "strip-pack-container"

    def __init__(self, containers=None, items=None, *, strip_pack_width=None):
        self._check_strip_pack(strip_pack_width)
        if not self._strip_pack:
            self._containers = Containers(containers, self)
        elif containers is not None:
            raise ContainersError(ContainersError.STRIP_PACK_ONLY)

        self._items = Items(items, self)

    def _check_strip_pack(self, strip_pack_width) -> None:
        """
        This method checks ``strip_pack_width`` value and set's initial values for:

            ``_strip_pack``: is the attribute modifying the problem. Used for \
            logic branching in execution. Affects:

                ``_construct``: Forces the method to accept ``container_height`` \
                as container's height.

                ``local_search``: by lowering the ``container_height`` in every new node.

                ``compare_solution``: Makes comparison check if all items are in solution.

                ``_containers._get_height``: Branches method to return solution height \
                or a minimum.

            ``_container_height``: is the actual container's height used
            in ``_construct``. Is also updated in every new node solution \
            in local_search, where a lower height is proven feasible.

            ``_container_min_height``: is the minimum height that the container \
            can get (not the solution height!).

            ``containers``: single container with preset height for strip packing mode.
        """
        self._container_min_height = None

        if strip_pack_width is None:
            self._strip_pack = False
            self._container_height = None
            self._heights_history = []
            return

        if not isinstance(strip_pack_width, int) or strip_pack_width <= 0:
            raise DimensionsError(DimensionsError.DIMENSION_VALUE)
        containers = {
            "strip-pack-container": {
                "W": strip_pack_width,
                "L": self.STRIP_PACK_INIT_HEIGHT,
            }
        }

        self._strip_pack = True
        self._container_height = self.MAX_W_L_RATIO * strip_pack_width
        self._containers = Containers(containers, self)

    def reset_container_height(self):
        """
        Resets the imaginary (strip packing) container's height.

        If called from bin-packing instace, nothing happens.
        """
        if self._strip_pack:
            self._container_height = (
                self.containers[self.STRIP_PACK_CONT_ID]["W"] * self.MAX_W_L_RATIO
            )
            self._container_min_height = None
        else:
            return


class PointGenerationSolver(
    BasePackingProblem,
    mixins.SolverPropertiesMixin,
    mixins.PointGenerationMixin,
):
    """
    Class that implements Point Generation solving.

    Extends problem's attributes to provide solving settings.
    """

    # settings defaults
    ROTATION_DEFAULT_VALUE = True
    # settings constraints
    PLOTLY_MIN_VER = ("5", "14", "0")
    PLOTLY_MAX_VER = ("6", "0", "0")
    KALEIDO_MIN_VER = ("0", "2", "1")
    KALEIDO_MAX_VER = ("0", "3", "0")

    def __init__(
        self, containers=None, items=None, settings=None, *, strip_pack_width=None
    ):
        super().__init__(
            containers=containers, items=items, strip_pack_width=strip_pack_width
        )

        self._rotation = None
        self._settings = settings or {}
        self.validate_settings()

        # it's the strategy used for the instance. It can be
        # dynamically changed to alter construction heuristic
        self._potential_points_strategy = self.DEFAULT_POTENTIAL_POINTS_STRATEGY
        self._containers_num = len(self._containers)
        self.solution = {}

    def _validate_settings(self) -> None:
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
        # SETTINGS FORMAT VALIDATION
        # % ----------------------------------------------------------------------------
        settings = self._settings
        if not isinstance(settings, dict):
            raise SettingsError(SettingsError.TYPE)

        # % ----------------------------------------------------------------------------
        # IF NO SETTINGS PROVIDED, SET DEFAULT VALUES FOR THESE ATTRIBUTES
        # % ----------------------------------------------------------------------------
        if not settings:
            # if no settings are provided, use DEFAULT values for these attributes
            self._rotation = self.ROTATION_DEFAULT_VALUE
            self._max_time_in_seconds = self.MAX_TIME_IN_SECONDS_DEFAULT_VALUE
            self._workers_num = self.WORKERS_NUM_DEFAULT_VALUE
            return

        # % ----------------------------------------------------------------------------
        # SETTINGS ROTATION
        # % ----------------------------------------------------------------------------
        rotation = settings.get("rotation")
        if rotation is not None:
            if not isinstance(rotation, bool):
                raise SettingsError(SettingsError.ROTATION_TYPE)
            self._rotation = rotation
        else:
            self._rotation = self.ROTATION_DEFAULT_VALUE

    def validate_settings(self) -> None:
        self._validate_settings()


class PointGenPack(
    PointGenerationSolver,
    mixins.SolutionFigureMixin,
    mixins.SolutionLoggingMixin,
):
    """
    This class enables total problem solution and
    depiction.
    """


class HyperPack(
    mixins.SolutionFigureMixin,
    PointGenerationSolver,
    mixins.LocalSearchMixin,
    mixins.ItemsManipulationMixin,
    mixins.SolutionLoggingMixin,
):
    """
    This class extends ``BasePointGenSolver``,
    utilizing its solving functionalities
    by implementing a hypersearch hyper-heuristic
    using the ``LocalSearchMixin``.

    Enables total problem solution and
    depiction.
    """

    # settings defaults
    MAX_TIME_IN_SECONDS_DEFAULT_VALUE = 60
    WORKERS_NUM_DEFAULT_VALUE = 1
    # setting for determining max neighbors parsing
    # before accepting node as optimum
    MAX_NEIGHBORS_THROTTLE = 2500
    # Potential points strategies constant suffix
    STRATEGIES_SUFFIX = ("A__", "B__", "F", "E")
    STRATEGIES_SUFFIX_STRIPACK = ("B__", "A__", "F", "E")

    def __init__(
        self, containers=None, items=None, settings=None, *, strip_pack_width=None
    ):
        self._max_time_in_seconds = None
        self._workers_num = None

        super().__init__(
            containers=containers,
            items=items,
            settings=settings,
            strip_pack_width=strip_pack_width,
        )

    def _validate_settings(self) -> None:
        super()._validate_settings()

        # % ----------------------------------------------------------------------------
        # SETTINGS MAX TIME IN SECONDS
        # % ----------------------------------------------------------------------------
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
        # % ----------------------------------------------------------------------------
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
