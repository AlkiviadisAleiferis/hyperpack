from time import time
from multiprocessing import Process, Queue
from .exceptions import MultiProcessError
from .loggers import hyperLogger
from copy import deepcopy


class HyperSearchProcess(Process):
    """
    HyperSearch Process used for multi processing hypersearching.
    Each process is given a set of potential points strategies, and
    hyper-searches for the given strategies.

    The search process is coordinated with the other deployed processes
    using the common array (shared_array). If one of the processes finds
    maximum value, the process stops and returns.

    Another criterion for stopping is the max available time.
    """

    def __init__(
        self,
        index,
        containers,
        items,  # passed items are already sorted
        settings,
        strategies_chunk,
        name,
        start_time,
        shared_array,
        throttle=True,
        *,
        strip_pack=False,
        container_min_height=None,
        _force_raise_error_index=None,
    ):
        super().__init__()
        from .heuristics import HyperPack

        self.throttle = throttle
        self._force_raise_error_index = _force_raise_error_index
        self.index = index
        self.shared_array = shared_array
        self.queue = Queue()
        self.strategies_chunk = strategies_chunk

        settings = deepcopy(settings)
        if "workers_num" in settings:
            settings["workers_num"] = 1
        params = {"items": items, "settings": settings}

        if strip_pack:
            params.update({"strip_pack_width": containers["strip-pack-container"]["W"]})
        else:
            params.update({"containers": containers})

        self.instance = HyperPack(**params)
        self.instance._container_min_height = container_min_height
        self.instance.start_time = start_time
        # it is the processe's name
        self.name = name

    def run(self):
        try:
            if self._force_raise_error_index in (self.index, "all"):
                raise MultiProcessError("testing error")

            retain_solution = self.instance.get_init_solution()
            best_obj_value = self.instance.calculate_obj_value()
            best_strategy = None
            optimum_obj_value = self.instance.get_optimum_objective_val()

            is_global = self.instance.global_check

            global_optima = False
            start_time = self.instance.start_time
            max_time_in_seconds = self.instance._max_time_in_seconds

            for strategy in self.strategies_chunk:
                # set the construction's heuristic potential points strategy
                self.instance._potential_points_strategy = strategy

                self.instance.local_search(throttle=self.throttle, _hypersearch=True)
                new_obj_value = self.instance.calculate_obj_value()
                array_optimum = self.instance._get_array_optimum(self.shared_array)

                if self.instance._check_solution(new_obj_value, best_obj_value):
                    best_obj_value = new_obj_value
                    self.shared_array[self.index] = new_obj_value

                    retain_solution = self.instance.get_solution()
                    best_strategy = [point for point in strategy]

                    # compare with all the processes and log
                    if is_global(new_obj_value, array_optimum):
                        hyperLogger.debug(
                            f"\t--Process {self.name} -->"
                            f"New best solution: {new_obj_value}\n"
                        )

                    global_optima = is_global(new_obj_value, optimum_obj_value)
                    if global_optima:
                        hyperLogger.debug(f"Process {self.name} acquired MAX objective value")
                        break

                # check if any process has reached global optimum
                global_optima = is_global(array_optimum, optimum_obj_value)
                out_of_time = time() - start_time > max_time_in_seconds

                if out_of_time:
                    hyperLogger.debug(f"Process {self.name}--> Exiting: surpassed max time")
                    break

                elif global_optima:
                    hyperLogger.debug(f"Process {self.name}--> Exiting: global optimum")
                    break

            output = (best_obj_value, *retain_solution, best_strategy)
            self.queue.put(output)

        # % ------------ Exception case -----------
        except Exception as e:
            hyperLogger.exception(f"Process {self.name} failed with error: \n\t{str(e)}\n")
            self.shared_array[self.index] = -1
            self.queue.put((-1, {}, {}, None))
