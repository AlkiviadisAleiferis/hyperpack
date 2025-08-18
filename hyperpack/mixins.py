import math
import sys
import time
from .abstract import AbstractLocalSearch
from .loggers import hyperLogger, logger
from . import constants

from .exceptions import (
    SettingsError,
    FigureExportError,
)
from array import array
from collections import deque
from copy import deepcopy
from pathlib import Path
import re


class PointGenerationMixin:
    """
    Mixin providing the point generation functionality.

    Attributes required for solving operation:
        ``_containers`` attribute of type ``Containers``.
        ``_items`` attribute of type ``Items``.
        ``_potential_points_strategy`` strategy attribute set pre-solving.
        ``_rotate`` attribute for rotation.
        ``_strip_pack`` attribute.
        ``_container_height`` attribute.
    """

    # solving constants
    DEFAULT_POTENTIAL_POINTS_STRATEGY = (
        "A_x",
        "A",
        "B_y",
        "B",
        "A_",  # A' point
        "B_",  # B' point
        "C",
        "C_y",  # C'y point
        "C_x",  # C'x point
        "C__"
    )
    INIT_POTENTIAL_POINTS = {
        "O": (0, 0),
        "A": deque(),
        "A_": deque(),
        "A_x": deque(),
        "B": deque(),
        "B_y": deque(),
        "B_": deque(),
        "C_y": deque(),
        "C_x": deque(),
        "C": deque(),
        "C__": deque(),
    }

    max_obj_value = 1
    init_obj_value = 0

    # % --------- construction heuristic methods ----------

    def _check_3d_fitting(self, W, L, H, Xo, Yo, Zo, w, l, h, current_items, requires_support=False, support_ratio=0.75, xy_planes=None) -> bool:
        """
        Checks if the item with coordinates (Xo, Yo, Zo)
        and dimensions (w, l, h) fits without colliding with any
        of the items currently in the container (current_items).

        Optionally, setting ``requires_support`` to True checks if 
        the item's bottom plane has at least ``support_ratio`` support 
        from items beneath it. ``xy_planes`` is mandatory in this case
        and holds all planes at the z-level of the item's bottom plane.
        """

        if requires_support and xy_planes is None:
            raise SettingsError(
                "xy_planes must be provided when requires_support is True"
            )
        
        # Check if the item fits within the container dimensions
        if(Xo + w > W or Yo + l > L or Zo + h > H):
            return False

        # Check for collisions with existing items
        for item_id in current_items:
            item = current_items[item_id]
            X, Y, Z = item["Xo"], item["Yo"], item["Zo"]
            w_, l_, h_ = item["w"], item["l"], item["h"]

            if item['rotation_state']:
                match item['rotation_state']:
                    case 1:  # rotate 90 degrees without changing base
                        w_, l_, h_ = l_, w_, h_
                    case 2: # change base to w x h
                        w_, l_, h_ = w_, h_, l_
                    case 3: # w x h base + rotate 90 degrees
                        w_, l_, h_ = h_, w_, l_
                    case 4: # change base to l x h
                        w_, l_, h_ = l_, h_, w_
                    case 5: # l x h base + rotate 90 degrees
                        w_, l_, h_ = h_, l_, w_
                    case _:
                        pass
            if (
                Xo + w > X and X + w_ > Xo and
                Yo + l > Y and Y + l_ > Yo and
                Zo + h > Z and Z + h_ > Zo
            ):
                return False
            
        if requires_support:
            percent_support = 0
            bottom_area = w * l
            for plane in xy_planes.get(Zo, []):
                intersecting_area = max(0, min(Xo + w, plane[1][0]) - max(Xo, plane[0][0])) * max(0, min(Yo + l, plane[1][1]) - max(Yo, plane[0][1]))
                percent_support += intersecting_area / bottom_area
            
            if percent_support < support_ratio:
                return False

        return True

    def _check_fitting(self, W, L, Xo, Yo, w, l, container_coords) -> bool:
        """
        Checks if all the coordinates of the item
        are not taken in `container_coords`.
        `container_coords` : [
            [int, int, ... W elements], # y-th coordinate
            .
            .
            .
            L lists, 1 for each coordinate
        ]
        """
        if (
            Xo + w > W
            or Yo + l > L
            or container_coords[Yo][Xo]
            or container_coords[Yo + l - 1][Xo]
            or container_coords[Yo][Xo + w - 1]
        ):
            return False

        for x in range(Xo, Xo + w - 1):
            if container_coords[Yo][x]:
                return False
        for y in range(Yo, Yo + l - 1):
            if container_coords[y][Xo]:
                return False

        return True

    def _generate_3d_points(
        self, container, xy_planes, xz_planes, yz_planes, potential_points, Xo, Yo, Zo, w, l, h, debug=False
    ) -> None:
        x, y, z = 0, 1, 2
        A = (Xo, Yo + l, Zo)
        B = (Xo + w, Yo, Zo)
        C = (Xo, Yo, Zo + h)

        L, W, H = container["L"], container["W"], container["H"]
        append_A = False
        append_B = False
        prohibit_A__and_E = False
        prohibit_B__and_F = False

        xz_less_than = [y_coord for y_coord in xz_planes if y_coord < Yo]
        yz_less_than = [x_coord for x_coord in yz_planes if x_coord < Xo]
        xy_below = [z_coord for z_coord in xy_planes if z_coord < Zo]

        # A point
        if A[y] < L and A[z] == 0:
            # A point on the bottom of the bin and within the bin length
            if debug:
                logger.debug(f"\tgen point A --> {A}")
            potential_points["A"].append(A)
        elif A[y] < L:
            # A point not on the bottom of the bin
            planes = xy_planes.get(A[z], [])
            for plane in planes:
                if plane[0][0] <= A[x] and plane[1][0] > A[x] and plane[0][1] <= A[y] and plane[1][1] > A[y]:
                    # if plane directly encompasses A from below
                    append_A = True
                    break
                # elif not prohibit_A__and_E and plane[1][1] == A[y] and plane[0][0] <= A[x] and plane[1][0] > A[x]:
                #     # if plane's Y ends directly under A
                #     prohibit_A__and_E = True
            if append_A:
                if debug:
                    logger.debug(f"\tgen point A --> {A}")
                potential_points["A"].append(A)

        # B point
        if B[x] < W and B[z] == 0:
            # B point on the bottom of the bin and within the bin length
            if debug:
                logger.debug(f"\tgen point B --> {B}")
            potential_points["B"].append(B)
        elif B[x] < W:
            # B point not on the bottom of the bin
            planes = xy_planes.get(B[z], [])
            for plane in planes:
                if plane[0][0] <= B[x] and plane[1][0] > B[x] and plane[0][1] <= B[y] and plane[1][1] > B[y]:
                    # if plane directly encompasses B from below
                    append_B = True
                    break
                # elif not prohibit_B__and_F and plane[1][0] == B[x] and plane[0][1] <= B[y] and plane[1][1] > B[y]:
                #     # if plane's X ends directly under B
                #     prohibit_B__and_F = True
            if append_B:
                if debug:
                    logger.debug(f"\tgen point B --> {B}")
                potential_points["B"].append(B)

        # A'x point (x-projection)
        append_A_x = False
        if append_A and yz_less_than != []:
            block = False
            for plane in yz_planes.get(Xo, []):
                if plane[0][0] <= A[y] and plane[1][0] > A[y] and plane[0][1] <= A[z] and plane[1][1] > A[z]:
                    # if plane directly encompasses A
                    block = True
                    break
            if not block:
                for x_coord in yz_less_than[-1::-1]:
                    planes = yz_planes.get(x_coord, [])
                    for plane in planes:
                        if plane[0][0] <= A[y] and plane[1][0] > A[y] and plane[0][1] <= A[z] and plane[1][1] > A[z]:
                            A_x = (x_coord, A[y], A[z])
                            if debug:
                                logger.debug(f"\tgen point A'x --> {A_x}")
                            potential_points["A_x"].append(A_x)
                            append_A_x = False
                            break
                    if append_A_x:
                        break
        
        # B'y point (y-projection)
        append_B_y = False
        if append_B and xz_less_than != []:
            block = False
            for plane in xz_planes.get(Yo, []):
                if plane[0][0] <= B[x] and plane[1][0] > B[x] and plane[0][1] <= B[z] and plane[1][1] > B[z]:
                    # if plane directly encompasses B
                    block = True
                    break
            if not block:
                for y_coord in xz_less_than[-1::-1]:
                    planes = xz_planes.get(y_coord, [])
                    for plane in planes:
                        if plane[0][0] <= B[x] and plane[1][0] > B[x] and plane[0][1] <= B[z] and plane[1][1] > B[z]:
                            B_y = (B[x], y_coord, B[z])
                            if debug:
                                logger.debug(f"\tgen point B'y --> {B_y}")
                            potential_points["B_y"].append(B_y)
                            append_B_y = True
                            break
                    if append_B_y:
                        break

        # A' point (z-projection)
        append_A_ = False
        if not append_A and not prohibit_A__and_E and A[y] < L and xy_below != []:
            # A' point
            for z_coord in xy_below[-1::-1]:
                planes = xy_planes.get(z_coord, [])
                for plane in planes:
                    if plane[0][0] <= A[x] and plane[1][0] > A[x] and plane[0][1] <= A[y] and plane[1][1] > A[y]:
                        A_ = (Xo, A[y], z_coord)
                        if debug:
                            logger.debug(f"\tgen point A' --> {A_}")
                        potential_points["A_"].append(A_)
                        append_A_ = True
                        break
                if append_A_:
                    break
        # B' point (z-projection)
        append_B_ = False
        if not append_B and not prohibit_B__and_F and B[x] < W and xy_below != []:
            # B' point
            for z_coord in xy_below[-1::-1]:
                planes = xy_planes.get(z_coord, [])
                for plane in planes:
                    if plane[0][0] <= B[x] and plane[1][0] > B[x] and plane[0][1] <= B[y] and plane[1][1] > B[y]:
                        B_ = (B[x], Yo, z_coord)
                        if debug:
                            logger.debug(f"\tgen point B' --> {B_}")
                        potential_points["B_"].append(B_)
                        append_B_ = True
                        break
                if append_B_:
                    break
        
        # C point
        append_C = False
        if C[z] < H and C[y] == 0 and C[x] == 0:
            if debug:
                logger.debug(f"\tgen point C --> {C}")
            potential_points["C"].append(C)
            append_C = True
        elif C[z] < H:
            planes = xz_planes.get(Yo, [])
            xz_check = False
            for plane in planes:
                if plane[0][0] <= C[x] and plane[1][0] > C[x] and plane[0][1] <= C[z] and plane[1][1] > C[z]:
                    # if plane directly encompasses C
                    xz_check = True
                    break
            if xz_check:
                planes = yz_planes.get(Xo, [])
                for plane in planes:
                    if plane[0][0] <= C[y] and plane[1][0] > C[y] and plane[0][1] <= C[z] and plane[1][1] > C[z]:
                        # if plane directly encompasses C
                        if debug:
                            logger.debug(f"\tgen point C --> {C}")
                        potential_points["C"].append(C)
                        append_C = True
                        break
    
        # C'y point (y-projection)
        append_C_y = False
        if not append_C and C[z] < H and xz_less_than != []:
            # C'y point
            for y_coord in xz_less_than[-1::-1]:
                planes = xz_planes.get(y_coord, [])
                for plane in planes:
                    if plane[0][0] <= C[x] and plane[1][0] > C[x] and plane[0][1] <= C[z] and plane[1][1] > C[z]:
                        C_y = (C[x], y_coord, C[z])
                        if debug:
                            logger.debug(f"\tgen point C'y --> {C_y}")
                        potential_points["C_y"].append(C_y)
                        append_C_y = True
                        break
                if append_C_y:
                    break
        
        # C'x point (x-projection)
        append_C_x = False
        if not append_C and C[z] < H and yz_less_than != []:
            # C'x point  
            for x_coord in yz_less_than[-1::-1]:
                planes = yz_planes.get(x_coord, [])
                for plane in planes:
                    if plane[0][0] <= C[y] and plane[1][0] > C[y] and plane[0][1] <= C[z] and plane[1][1] > C[z]:
                        C_x = (x_coord, C[y], C[z])
                        if debug:
                            logger.debug(f"\tgen point C'x --> {C_x}")
                        potential_points["C_x"].append(C_x)
                        append_C_x = True
                        break
                if append_C_x:
                    break

        # C'' point (when C is not in a corner)
        if C[z] < H and not append_C:
            if(debug):
                potential_points["C__"].append(C)
                logger.debug(f"\tgen point C'' --> {C}")

    def _get_current_point(self, potential_points) -> tuple:
        for pclass in self._potential_points_strategy:
            if potential_points[pclass]:
                return potential_points[pclass].popleft(), pclass

        return (None, None)

    def _append_planes(self, xy_planes, xz_planes, yz_planes, Xo, Yo, Zo, w, l, h):
        # xy planes
        if Zo in xy_planes:
            xy_planes[Zo].append(((Xo, Yo), (Xo + w, Yo + l)))
        else:
            xy_planes[Zo] = [((Xo, Yo), (Xo + w, Yo + l))]

        if Zo + h in xy_planes:
            xy_planes[Zo + h].append(((Xo, Yo), (Xo + w, Yo + l)))
        else:
            xy_planes[Zo + h] = [((Xo, Yo), (Xo + w, Yo + l))]

        # xz planes
        if Yo in xz_planes:
            xz_planes[Yo].append(((Xo, Zo), (Xo + w, Zo + h)))
        else:
            xz_planes[Yo] = [((Xo, Zo), (Xo + w, Zo + h))]

        if Yo + l in xz_planes:
            xz_planes[Yo + l].append(((Xo, Zo), (Xo + w, Zo + h)))
        else:
            xz_planes[Yo + l] = [((Xo, Zo), (Xo + w, Zo + h))]

        # yz planes
        if Xo in yz_planes:
            yz_planes[Xo].append(((Yo, Zo), (Yo + l, Zo + h)))
        else:
            yz_planes[Xo] = [((Yo, Zo), (Yo + l, Zo + h))]

        if Xo + w in yz_planes:
            yz_planes[Xo + w].append(((Yo, Zo), (Yo + l, Zo + h)))
        else:
            yz_planes[Xo + w] = [((Yo, Zo), (Yo + l, Zo + h))]

    def _get_initial_container_height(self, container):
        if self._strip_pack:
            return self._container_height
        else:
            return container["H"]

    def _get_initial_potential_points(self):
        return {
            "O": (0, 0, 0),
            "A": deque(),
            "B": deque(),
            "A_": deque(),
            "B_": deque(),
            "A_x": deque(),
            "B_y": deque(),
            "C": deque(),
            "C_y": deque(),
            "C_x": deque(),
            "C__": deque(),
        }

    def get_initial_xy_planes(self, W, L, H):
        return {0: [((0, 0), (W, L))], H: [((0, 0), (W, L))]}
    
    def get_initial_xz_planes(self, W, L, H):
        return {0: [((0, 0), (W, H))], L: [((0, 0), (W, H))]}
    
    def get_initial_yz_planes(self, W, L, H):
        return {0: [((0, 0), (L, H))], W: [((0, 0), (L, H))]}

    def _get_initial_point(self, potential_points, **kwargs):
        return potential_points["O"], "O"

    def calculate_objective_value(
        self, obj_value, w, l, h, W, L, H
    ):
        return obj_value + (w * l * h) / (W * L * H)

    def _construct_solution(self, container, items, debug=False) -> tuple:
        """
        Point generation construction heuristic
        for solving single container problem instance.

        INPUT
            container,
            items,
            debug (mode),

            implicitly by attribute, the potential points strategy

        OUTPUT
            A. returns current_solution with the solution of the container.
            B. returns (remaining non-fitted items, containers utilization) tuple.
        """
        current_solution = {}
        strip_pack = getattr(self, "_strip_pack", False)

        # 'items' are the available for placement
        # after an item get's picked, it gets removed
        items_ids = [_id for _id in items]

        L = container["L"]
        W = container["W"]
        H = self._get_initial_container_height(container)

        # obj_value is the container utilization
        # obj_value = Volume(Placed Items)/Volume(Container)
        obj_value = self.init_obj_value
        max_obj_value = self.max_obj_value

        xy_planes = self.get_initial_xy_planes(W, L, H)
        xz_planes = self.get_initial_xz_planes(W, L, H)
        yz_planes = self.get_initial_yz_planes(W, L, H)

        potential_points = self._get_initial_potential_points()

        # O(0, 0, 0) init point
        current_point, point_class = self._get_initial_point(potential_points)

        # START of item placement process
        while True:
            if (current_point is None) or (not items_ids) or (obj_value >= max_obj_value):
                break

            if debug:
                logger.debug(f"\nCURRENT POINT: {current_point} class: {point_class}")

            Xo, Yo, Zo = current_point

            # CURRENT POINT'S ITEM SEARCH
            # get first fitting in sequence
            for item_id in items_ids:
                item = items[item_id]
                w, l, h, rotation_orientation = item["w"], item["l"], item["h"], 0

                check = self._check_3d_fitting(W, L, H, Xo, Yo, Zo, w, l, h, current_solution, requires_support=True, xy_planes=xy_planes)
                if not check:
                    if self._rotation:
                        for rotation_state in range(1, 6):
                            match rotation_state:
                                case 1:  # rotate 90 degrees without changing base
                                    w, l, h = item["l"], item["w"], item["h"]
                                case 2: # change base to w x h
                                    w, l, h = item["w"], item["h"], item["l"]
                                case 3: # w x h base + rotate 90 degrees
                                    w, l, h = item["h"], item["w"], item["l"]
                                case 4: # change base to l x h
                                    w, l, h = item["l"], item["h"], item["w"]
                                case 5: # l x h base + rotate 90 degrees
                                    w, l, h = item["h"], item["l"], item["w"]
                            
                            check = self._check_3d_fitting(W, L, H, Xo, Yo, Zo, w, l, h, current_solution, requires_support=True, xy_planes=xy_planes)
                            if check:
                                rotation_orientation = rotation_state
                                break

                        if not check:
                            continue
                    else:
                        continue

                if debug:
                    logger.debug(f"--> {item_id}\n")

                # removing item wont affect execution. 'for' breaks below
                items_ids.remove(item_id)
                del items[item_id]

                if not strip_pack:
                    obj_value = self.calculate_objective_value(
                        obj_value,
                        w,
                        l,
                        h,
                        W,
                        L,
                        H,
                    )

                item.update({"Xo": Xo, "Yo": Yo, "Zo": Zo, "rotation_state": rotation_orientation})
                current_solution[item_id] = item

                self._generate_3d_points(
                    container,
                    xy_planes,
                    xz_planes,
                    yz_planes,
                    potential_points,
                    Xo,
                    Yo,
                    Zo,
                    w,
                    l,
                    h,
                    debug=False,
                )

                self._append_planes(xy_planes, xz_planes, yz_planes, Xo, Yo, Zo, w, l, h)

                break

            if debug:
                self._current_potential_points = deepcopy(potential_points)

            current_point, point_class = self._get_current_point(potential_points)

        # END of item placement process

        if strip_pack:
            height_of_solution = max(set(horizontals)) or 1
            items_area = sum(
                [item["w"] * item["l"] for _, item in current_solution.items()]
            )
            obj_value = items_area / (W * height_of_solution)

        return items, obj_value, current_solution

    def _get_container_solution(self, current_solution):
        """
        Returns the solution object of the _construct method
        for the current solving container.
        """
        solution = {}
        for _id in current_solution:
            item = current_solution[_id]
            w_, l_, h_ = item["w"], item["l"], item["h"]
            match item['rotation_state']:
                    case 1:  # rotate 90 degrees without changing base
                        w_, l_, h_ = l_, w_, h_
                    case 2: # change base to w x h
                        w_, l_, h_ = w_, h_, l_
                    case 3: # w x h base + rotate 90 degrees
                        w_, l_, h_ = h_, w_, l_
                    case 4: # change base to l x h
                        w_, l_, h_ = l_, h_, w_
                    case 5: # l x h base + rotate 90 degrees
                        w_, l_, h_ = h_, l_, w_
                    case _:
                        pass
            solution[_id] = [
                item["Xo"],
                item["Yo"],
                item["Zo"],
                w_,
                l_,
                h_
            ]
        return solution

    def _solve(self, sequence=None, debug=False) -> None:
        """
        Solves for all the containers, using the
        `point generation construction heuristic
        <https://github.com/AlkiviadisAleiferis/hyperpack-theory/>`_.

        **OPERATION**
            Populates ``solution`` with solution found for every container.

            Populates ``obj_val_per_container`` with the utilization \
            of every container.

        **PARAMETERS**
            ``sequence`` : the sequence of ids to create the items to solve for. \
            If None, ``items`` will be used. Items used for solving are deepcopied \
            from ``items`` with corresponding sequence.

            ``debug`` : If True, debuging mode will be enabled, usefull \
            only for developing.

        **RETURNS**
            ``solution`` , ``obj_val_per_container``

        **NOTES**
            Solution is deterministic, and solely dependent on these factors:

                ``potential_points_strategy`` attribute for the potential points strategy.

                ``items_sequence`` **sequence** of the items ids.
        """
        # deepcopying is done cause items will be removed
        # from items pool after each container is solved
        # self._items shouldn't have same ids with items
        if sequence is None:
            items = self._items.deepcopy()
        else:
            items = self._items.deepcopy(sequence)

        obj_val_per_container = {}
        solution = {}

        for cont_id in self._containers:
            solution[cont_id] = {}
            obj_val_per_container[cont_id] = 0
            if items == {}:
                continue
            items, util, current_solution = self._construct_solution(
                container=self._containers[cont_id], items=items, debug=debug
            )
            obj_val_per_container[cont_id] = util
            solution[cont_id] = self._get_container_solution(current_solution)

        return solution, obj_val_per_container


class SolutionLoggingMixin:
    """
    Mixin for logging the solution.
    """

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
            L = self._containers[cont_id]["L"]
            W = self._containers[cont_id]["W"]
            H = self._containers._get_height(cont_id)
            log.append(f"Container: {cont_id} {W}x{L}x{H}")
            total_items_volume = sum(
                [i[3] * i[4] * i[5] for _, i in self.solution[cont_id].items()]
            )
            log.append(f"\t[util%] : {total_items_volume*100/(W*L*H):.4f}%")
            if self._strip_pack:
                solution = self.solution[cont_id]
                # height of items stack in solution
                max_height = max(
                    [solution[item_id][2] + solution[item_id][5] for item_id in solution] # Zo + h = total height
                    or [0]
                )
                log.append(f"\t[max height] : {max_height}")

        items_ids = {_id for cont_id, items in self.solution.items() for _id in items}
        remaining_items = [_id for _id in self._items if _id not in items_ids]
        log.append(f"\nRemaining items : {remaining_items}")
        output_log = "\n".join(log)
        hyperLogger.info(output_log)
        return output_log


class SolutionFigureMixin:
    """
    Mixin implementing the methods for building the
    figures of the solution.

    Extends the settings validation to support the
    figure operation.

    Must be used on leftmost position in the inheritance.
    """

    FIGURE_FILE_NAME_REGEX = re.compile(r"[a-zA-Z0-9_-]{1,45}$")
    FIGURE_DEFAULT_FILE_NAME = "PlotlyGraph"
    ACCEPTED_IMAGE_EXPORT_FORMATS = ("pdf", "png", "jpeg", "webp", "svg")
    # settings constraints
    PLOTLY_MIN_VER = ("5", "14", "0")
    PLOTLY_MAX_VER = ("6", "0", "0")
    KALEIDO_MIN_VER = ("0", "2", "1")
    KALEIDO_MAX_VER = ("0", "3", "0")

    def _check_plotly_kaleido_versions(self) -> None:
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

    def _validate_figure_settings(self) -> None:
        self._check_plotly_kaleido_versions()

        figure_settings = self._settings.get("figure", {})

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
            if not isinstance(show, bool):
                raise SettingsError(SettingsError.FIGURE_SHOW_VALUE)

    def colorgen(self, index) -> str:
        """
        Method for returning a hexadecimal color for every item
        in the graph.
        """
        return constants.ITEMS_COLORS[index]

    def create_figure(self, show=False) -> None:
        """
        Method used for creating figures and showing/exporting them.

        **WARNING**
            plotly library at least 5.14.0 must be installed in environment,
            and for image exportation, at least kaleido 0.2.1.

            See :ref:`here<figures_guide>` for
            detailed explanation of the method.

        **OPERATION**
            Create's the solution's figure.

        **PARAMETERS**
            ``show``: if True, the created figure will be displayed in browser \
            after creation.
        """

        if not self.solution:
            hyperLogger.warning(FigureExportError.NO_SOLUTION_WARNING)
            return

        if not self._plotly_installed:
            raise SettingsError(SettingsError.PLOTLY_NOT_INSTALLED)

        elif not self._plotly_ver_ok:
            raise SettingsError(SettingsError.PLOTLY_VERSION)

        else:
            import plotly

            go = plotly.graph_objects

        figure_settings = self._settings.get("figure", {})
        export = figure_settings.get("export")
        show = figure_settings.get("show") or show

        if not show and export is None:
            hyperLogger.warning(FigureExportError.NO_FIGURE_OPERATION)
            return

        containers_ids = tuple(self._containers)

        for cont_id in containers_ids:
            W, L, H = self._containers[cont_id]["W"], self._containers[cont_id]["L"], self._containers._get_height(cont_id)
            box_traces = []
            for item_id in self.solution[cont_id]:
                item = self.solution[cont_id][item_id]
                Xo, Yo, Zo, w, l, h = item[0], item[1], item[2], item[3], item[4], item[5]

                vertices = [
                    (Xo, Yo, Zo),
                    (Xo + w, Yo, Zo),
                    (Xo + w, Yo + l, Zo),
                    (Xo, Yo + l, Zo),
                    (Xo, Yo, Zo + h),
                    (Xo + w, Yo, Zo + h),
                    (Xo + w, Yo + l, Zo + h),
                    (Xo, Yo + l, Zo + h)
                ]

                box_trace = go.Mesh3d(
                    x=[vertex[0] for vertex in vertices],
                    y=[vertex[1] for vertex in vertices],
                    z=[vertex[2] for vertex in vertices],
                    i=[0, 2, 4, 6, 0, 5, 3, 6, 0, 7, 1, 6],
                    j=[1, 3, 5, 7, 1, 4, 2, 7, 3, 4, 2, 5],
                    k=[2, 0, 6, 4, 5, 0, 6, 3, 7, 0, 6, 1],
                    name=item_id,
                    showlegend=True
                )
                box_traces.append(box_trace)

            fig = go.Figure(data=box_traces)

            fig.update_layout(
            title_text='3D Render of Boxes with Plotly',
            scene=dict(
                xaxis=dict(range=[0, W]),
                yaxis=dict(range=[0, L]),
                zaxis=dict(range=[0, H]),
                aspectratio=dict(x=W/(W+L), y=L/(W+L), z=H/(W+L)),
            ),
            margin=dict(l=0, r=0, b=0, t=40),
)

            if export:
                try:
                    export_type = export.get("type", "html")
                    export_path = Path(export["path"])
                    file_name = export.get("file_name", "")

                    if export_type == "html":
                        fig.write_html(export_path / f"{file_name}__{cont_id}.html")

                    elif export_type == "image":
                        import plotly.io as pio

                        file_format = export["format"]
                        width = export.get("width") or 1700
                        height = export.get("height") or 1700
                        scale = 1
                        pio.kaleido.scope.default_width = width
                        pio.kaleido.scope.default_height = height
                        pio.kaleido.scope.default_scale = scale
                        fig.write_image(
                            export_path / f"{file_name}__{cont_id}.{file_format}"
                        )

                except Exception as e:
                    error_msg = FigureExportError.FIGURE_EXPORT.format(e)
                    raise FigureExportError(error_msg)
            if show:
                fig.show(config={"responsive": False})

    def validate_settings(self) -> None:
        self._validate_settings()
        self._validate_figure_settings()


class ItemsManipulationMixin:
    """
    Mixin providing ``items`` manipulation methods.
    """

    def orient_items(self, orientation: str or None = "short") -> None:
        """
        Method for orienting the ``items`` structure.

        **OPERATION**
            Orients each item in items set by rotating it
            (interchange w, l, h of item).

            See :ref:`here<orient_items>` for
            detailed explanation of the method.

        **PARAMETERS**
            ``orientation`` : "short"/"tall". If None provided, \
            orientation will be skipped.

        **WARNING**
            Changing the values of ``self.items`` causes
            resetting of the ``solution`` attribute.
        """
        if orientation is None:
            return

        if not self._rotation:
            hyperLogger.warning("can't rotate items. Rotation is disabled")
            return

        items = self._items

        if orientation not in ("short", "tall"):
            hyperLogger.warning(
                f"orientation parameter '{orientation}' not valid. Orientation skipped."
            )
            return

        for _id in items:
            w, l, h = items[_id]["w"], items[_id]["l"], items[_id]["h"]

            if orientation == "short":
                if h > w:
                    h, w = w, h
                if h > l:
                    h, l = l, h
                items[_id]["w"], items[_id]["l"], items[_id]["h"] = w, l, h

            elif orientation == "tall":
                if h < l:
                    h, l = l, h
                if h < w:
                    h, w = w, h
                items[_id]["w"], items[_id]["l"], items[_id]["h"] = w, l, h

    def sort_items(self, sorting_by: tuple or None = ("volume", True)) -> None:
        """
        Method for ordering the ``items`` structure. See :ref:`here<sort_items>` for
        detailed explanation of the method.

        **OPERATION**
            Sorts the ``items``

            according to ``sorting_by`` parameter guidelines.

        **PARAMETERS**
            ``sorting_by`` : (sorting criterion, reverse). If None provided, sorting
            will be skipped.

        **WARNING**
            Changing the values of ``items`` causes resetting of the
            ``solution`` attribute.

        **RETURNS**
            ``None``
        """
        if sorting_by is None:
            return

        by, reverse = sorting_by

        items = self._items.deepcopy()

        if by == "volume":
            sorted_items = [[i["w"] * i["l"] * i["h"], _id] for _id, i in items.items()]
            sorted_items.sort(reverse=reverse)
        elif by == "surface_area":
            sorted_items = [[2 * i["w"] * i["l"] + 2 * i["w"] * i["h"] + 2 * i["l"] * i["h"], _id] for _id, i in items.items()]
            sorted_items.sort(reverse=reverse)
        elif by == "longest_side_ratio":
            sorted_items = [
                [max(i["w"], i["l"], i["h"]) / min(i["w"], i["l"], i["h"]), _id]
                for _id, i in items.items()
            ]
            sorted_items.sort(reverse=reverse)
        else:
            raise NotImplementedError

        self.items = {el[1]: items[el[1]] for el in sorted_items}


class DeepcopyMixin:
    """
    Mixin class providing copy/deepcopy utilities for
    certain attributes.
    """

    def _copy_objective_val_per_container(self, obj_val_per_container=None):
        if obj_val_per_container is None:
            obj_val_per_container = self.obj_val_per_container
        return {
            cont_id: obj_val_per_container[cont_id] for cont_id in obj_val_per_container
        }

    def _deepcopy_solution(self, solution=None):
        if solution is None:
            solution = self.solution
        return {
            cont_id: {
                item_id: [data for data in solution[cont_id].get(item_id, [])]
                for item_id in self._items
                if solution[cont_id].get(item_id) is not None
            }
            for cont_id in self._containers
        }


class LocalSearchMixin(AbstractLocalSearch, DeepcopyMixin):
    """
    Mixin implementing the Local Search.
    """

    def evaluate_node(self, sequence):
        self.solve(sequence=sequence, debug=False)

    def get_solution(self):
        return (
            self._deepcopy_solution(),
            self._copy_objective_val_per_container(),
        )

    def calculate_obj_value(self):
        """
        Calculates the objective value based on 3D volume utilization across multiple containers.
        It encourages filling containers sequentially by weighting the last container's
        utilization less. A penalty is also added for the volume-weighted Z-center of mass
        to favor solutions that place larger items lower.
        """
        if not self.solution:
            return 0

        container_utilizations = []
        container_penalties = []

        # Iterate through each container that has a solution
        for cont_id in self.solution:
            container = self._containers[cont_id]
            solution_items = self.solution[cont_id]

            # Skip containers that are part of the problem but unused in this solution
            if not solution_items:
                container_utilizations.append(0)
                container_penalties.append(0)
                continue

            H = self._get_initial_container_height(container)
            total_container_volume = container["W"] * container["L"] * H
            
            total_items_volume = 0
            weighted_z_sum = 0

            for item_id, item_data in solution_items.items():
                # item_data from solution is [Xo, Yo, Zo, w, l, h]
                item_volume = item_data[3] * item_data[4] * item_data[5]
                total_items_volume += item_volume
                weighted_z_sum += item_volume * item_data[2]

            # Calculate utilization and penalty for this specific container
            utilization = total_items_volume / total_container_volume
            container_utilizations.append(utilization)

            penalty = 0
            if total_items_volume > 0:
                center_of_mass_z = weighted_z_sum / total_items_volume
                normalized_penalty = center_of_mass_z / H
                penalty_factor = 0.001  # Small factor to act as a tie-breaker
                penalty = penalty_factor * normalized_penalty
            container_penalties.append(penalty)

        # Aggregate the results from all containers
        base_objective = 0
        if len(container_utilizations) == 1:
            base_objective = container_utilizations[0]
        elif len(container_utilizations) > 1:
            # encourages filling earlier bins before using the last one
            base_objective = sum(container_utilizations[:-1]) + 0.7 * container_utilizations[-1]

        total_penalty = sum(container_penalties)
        
        return base_objective - total_penalty

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

    def compare_node(self, new_obj_value, best_obj_value):
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
