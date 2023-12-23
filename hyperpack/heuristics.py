import math
import re
import sys
import time
from collections import deque
from itertools import permutations
from multiprocessing import Array
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
    mixins.PointGenSolverMixin,
    mixins.DeepcopyMixin,
    mixins.FigureBuilderMixin,
    mixins.PropertiesMixin,
    mixins.StripPackMixin,
    mixins.SettingsMixin,
    mixins.SolutionLoggingMixin,
    mixins.StructuresUtilsMixin,
):
    """
    Base class for initiating the problem
    and grouping the mixins for solving.
    """

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
        self._check_plotly_kaleido_versions()
        self.validate_settings()

        # it's the strategy used for the instance. It can be
        # dynamically changed to alter construction heuristic
        self._potential_points_strategy = self.DEFAULT_POTENTIAL_POINTS_STRATEGY
        self._containers_num = len(self._containers)
        self.solution = {}


class HyperPack(PointGenPack, mixins.LocalSearchMixin):
    """
    This class extends ``PointGenPack``,
    utilizing its solving functionalities
    by implementing a hypersearch hyper-heuristic
    using the ``LocalSearchMixin`` mixin.
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
