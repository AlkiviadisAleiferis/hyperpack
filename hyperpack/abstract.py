from .loggers import hyperLogger
from itertools import combinations
from time import time


class AbstractLocalSearch:
    """
    An abstraction for implementing a N-opt local search,
    either 'greedy-descent' or 'hill-climbing'.
    """

    # "MAX" or "MIN" -> 'hill-climbing' or 'greedy-descent'
    OPTIMIZATION = "MAX"
    MAX_NEIGHBORS_THROTTLE = 2500
    # TODO: implement
    OPT_NUM = 2
    logger = hyperLogger

    def get_init_solution(self):
        raise NotImplementedError

    def calculate_obj_value(self):
        raise NotImplementedError

    def get_solution(self):
        raise NotImplementedError

    def get_max_neighbors_num(self, throttle, seq_length):
        max_constant = getattr(self, "MAX_NEIGHBORS_THROTTLE", float("inf"))
        max_neighbors_num = seq_length * (seq_length - 1) / 2
        if throttle and max_neighbors_num > max_constant:
            return max_constant
        else:
            return max_neighbors_num

    def get_optimum_objective_val(self):
        """
        Returns the optimum objective value achievable.
        """
        if getattr(self, "OPTIMIZATION") == "MAX":
            return float("inf")
        else:
            return -float("inf")

    def global_check(self, value: float, optimum_value: float):
        if getattr(self, "OPTIMIZATION") == "MAX":
            return value >= optimum_value
        else:
            return value <= optimum_value

    def node_check(self, new_obj_value, best_obj_value):
        if getattr(self, "OPTIMIZATION") == "MAX":
            return new_obj_value > best_obj_value
        else:
            return new_obj_value < best_obj_value

    def evaluate(self, sequence):
        raise NotImplementedError

    def debug_local_search(self, **kwargs):
        """
        Debug logging after operation. Default implementation.
        Override for customization.
        """
        node_num = kwargs["node_num"]
        neighbor_found = kwargs["neighbor_found"]
        best_obj_value = kwargs["best_obj_value"]
        processed_neighbors = kwargs["processed_neighbors"]
        out_of_time = kwargs["out_of_time"]
        global_optima = kwargs["global_optima"]

        if not neighbor_found:
            self.logger.debug("-- no new node")
        else:
            self.logger.debug("-- new node found")
        self.logger.debug(f"\tnode num: {node_num}")
        self.logger.debug(f"\tbest obj_val: {best_obj_value}")
        self.logger.debug(f"\tprocessed_neighbors : {processed_neighbors}\n")
        if out_of_time:
            self.logger.debug("-- out of time - exiting")
        elif not neighbor_found:
            self.logger.debug("-- no new node found - local optima - exiting")
        elif global_optima:
            self.logger.debug("-- global optimum found - exiting")

    def local_search(
        self,
        init_sequence,
        throttle,
        start_time,
        max_time_in_seconds,
        debug=True,
    ):
        # initial data
        retain_solution = self.get_init_solution()
        best_obj_value = self.calculate_obj_value()
        optimum_obj_value = self.get_optimum_objective_val()

        node_seq = init_sequence
        node_num = 0
        seq_length = len(node_seq)
        swaps = list(combinations(range(seq_length), self.OPT_NUM))
        max_neighbors_num = self.get_max_neighbors_num(throttle, seq_length)

        if hasattr(self, "init_operations"):
            self.init_operations()

        continue_criterion = True
        while continue_criterion:
            node_num += 1
            out_of_time, neighbor_found, global_optima = (
                False,
                False,
                False,
            )
            processed_neighbors = 0

            # start of neighborhood search
            # traverse each neighbor of node
            for swap in swaps:
                # create new sequence
                current_seq = [el for el in node_seq]
                i, j = swap
                current_seq[i], current_seq[j] = current_seq[j], current_seq[i]

                # should update `self.solution` instance attribute
                # or objective value related attributes and instance state
                self.evaluate(sequence=current_seq)
                new_obj_value = self.calculate_obj_value()

                processed_neighbors += 1

                if self.node_check(new_obj_value, best_obj_value):
                    # set new node
                    node_seq = [el for el in current_seq]
                    best_obj_value = new_obj_value

                    # possible deepcopying mechanism to retain solution state
                    retain_solution = self.get_solution()

                    if hasattr(self, "extra_node_operations"):
                        self.extra_node_operations()

                    # criteria update
                    neighbor_found = True
                    global_optima = self.global_check(best_obj_value, optimum_obj_value)

                # criteria update
                out_of_time = time() - start_time >= max_time_in_seconds
                max_neighbors = processed_neighbors >= max_neighbors_num

                if out_of_time or neighbor_found or global_optima or max_neighbors:
                    break
            # end of neighborhood search

            if debug:
                self.debug_local_search(
                    node_num=node_num,
                    best_obj_value=best_obj_value,
                    processed_neighbors=processed_neighbors,
                    out_of_time=out_of_time,
                    global_optima=global_optima,
                    neighbor_found=neighbor_found,
                )

            # update continue criterion
            continue_criterion = neighbor_found and not out_of_time and not global_optima
        # END of local search
        return retain_solution
