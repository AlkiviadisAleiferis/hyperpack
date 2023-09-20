import math
import platform
import re
import sys
import time
from copy import deepcopy
from itertools import permutations
from multiprocessing import Array, Process, Queue, cpu_count, current_process
from pathlib import Path

from . import constants
from .exceptions import (
    ContainersError,
    FigureExportError,
    ItemsError,
    MultiProcessError,
    PotentialPointsError,
    SettingsError,
)
from .loggers import hyperLogger, logger
from .structures import Containers, Items

ITEMS_COLORS = constants.ITEMS_COLORS


class PointGenPack:
    """
    This class implements the Point Generation solution
    construction heuristic, along many auxiliary methods.
    """

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
        "A": [],
        "B": [],
        "A_": [],
        "B_": [],
        "A__": [],
        "B__": [],
        "C": [],
        "D": [],
        "E": [],
        "F": [],
    }
    # settings defaults
    MAX_TIME_IN_SECONDS_DEFAULT_VALUE = 60
    WORKERS_NUM_DEFAULT_VALUE = 1
    ROTATION_DEFAULT_VALUE = True
    FIGURE_FILE_NAME_REGEX = re.compile(r"[a-zA-Z0-9_-]{1,45}$")
    FIGURE_DEFAULT_FILE_NAME = "PlotlyGraph"
    ACCEPTED_IMAGE_EXPORT_FORMATS = ("pdf", "png", "jpeg", "webp", "svg")
    PLOTLY_MIN_VER = ("5", "14", "0")
    PLOTLY_MAX_VER = ("6", "0", "0")
    KALEIDO_MIN_VER = ("0", "2", "1")
    KALEIDO_MAX_VER = ("0", "3", "0")

    def __init__(self, containers=None, items=None, settings=None):
        self._containers = Containers(containers, self)
        self._items = Items(items, self)

        self._max_time_in_seconds = None
        self._workers_num = None
        self._rotation = None
        self._settings = settings or {}
        self.validate_settings()

        # it's the strategy used for the instance. It can be
        # dynamically changed to alter construction heuristic
        self._potential_points_strategy = self.DEFAULT_POTENTIAL_POINTS_STRATEGY
        self._containers_num = len(containers)
        self.solution = {}  # {container_id: solution, ...}

    def validate_settings(self) -> None:
        """
        Method for validating and applying the settings either
        provided through instantiation or explicit assignment to
        self.settings, or by calling ``self.validate_settings`` by the user.

        **PARAMETERS**
            ``None``

        **OPERATION**
            - Validates ``settings`` instance attribute data structure and format.
            - Applies said settings to correlated private attributes.

        **RETURNS**
            `None`
        """

        # % ----------------------------------------------------------------------------
        # SETTINGS VALIDATION
        settings = self._settings
        if not isinstance(settings, dict):
            raise SettingsError("TYPE")

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
            raise SettingsError("MAX_TIME_IN_SECONDS_TYPE")

        if max_time_in_seconds < 1:
            raise SettingsError("MAX_TIME_IN_SECONDS_VALUE")
        self._max_time_in_seconds = max_time_in_seconds

        # % ----------------------------------------------------------------------------
        # SETTINGS WORKERS NUM
        workers_num = self._settings.get("workers_num")
        if workers_num is not None:
            try:
                if not workers_num > 0:
                    raise SettingsError("WORKERS_NUM_VALUE")
            except Exception:
                raise SettingsError("WORKERS_NUM_VALUE")
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
                raise SettingsError("ROTATION_TYPE")
            self._rotation = rotation
        else:
            self._rotation = self.ROTATION_DEFAULT_VALUE

        # % ----------------------------------------------------------------------------
        # FIGURE SETTINGS VALIDATION
        figure_settings = settings.get("figure", {})

        if not isinstance(figure_settings, dict):
            raise SettingsError("FIGURE_KEY_TYPE")

        if figure_settings:
            # plotly library must be installed, and at least 5.14.0 version
            # to enable any figure instantiation/exportation
            try:
                import plotly
            except ImportError:
                raise SettingsError("PLOTLY_NOT_INSTALLED")

            plotly_ver = tuple([x for x in plotly.__version__.split(".")][:3])
            if plotly_ver < self.PLOTLY_MIN_VER or plotly_ver >= self.PLOTLY_MAX_VER:
                raise SettingsError("PLOTLY_VERSION")

            if "export" in figure_settings:
                export = figure_settings.get("export")

                if not isinstance(export, dict):
                    raise SettingsError("FIGURE_EXPORT_VALUE_TYPE")

                export_type = export.get("type")
                if export_type is None:
                    raise SettingsError("FIGURE_EXPORT_TYPE_MISSING")

                if export_type not in ("html", "image"):
                    raise SettingsError("FIGURE_EXPORT_TYPE_VALUE")

                export_path = export.get("path")
                if export_path is None:
                    raise SettingsError("FIGURE_EXPORT_PATH_MISSING")

                if not isinstance(export_path, str):
                    raise SettingsError("FIGURE_EXPORT_PATH_VALUE")

                export_path = Path(export_path)
                if not export_path.exists():
                    raise SettingsError("FIGURE_EXPORT_PATH_NOT_EXISTS")

                if not export_path.is_dir():
                    raise SettingsError("FIGURE_EXPORT_PATH_NOT_DIRECTORY")

                file_format = export.get("format")
                if file_format is None and export_type != "html":
                    raise SettingsError("FIGURE_EXPORT_FORMAT_MISSING")

                if export_type != "html" and not isinstance(file_format, str):
                    raise SettingsError("FIGURE_EXPORT_FORMAT_TYPE")

                accepted_formats = self.ACCEPTED_IMAGE_EXPORT_FORMATS
                if export_type == "image" and file_format not in accepted_formats:
                    raise SettingsError("FIGURE_EXPORT_FORMAT_VALUE")

                file_name = export.get("file_name", None)
                if file_name is None:
                    self._settings["figure"]["export"][
                        "file_name"
                    ] = self.FIGURE_DEFAULT_FILE_NAME
                else:
                    if not isinstance(file_name, str):
                        raise SettingsError("FIGURE_EXPORT_FILE_NAME_TYPE")

                    if not self.FIGURE_FILE_NAME_REGEX.match(file_name):
                        raise SettingsError("FIGURE_EXPORT_FILE_NAME_VALUE")

                if export_type == "image":
                    try:
                        import kaleido
                    except ImportError:
                        raise SettingsError("FIGURE_EXPORT_KALEIDO_MISSING")

                    kaleido_ver = tuple([x for x in kaleido.__version__.split(".")][:3])
                    if (
                        kaleido_ver < self.KALEIDO_MIN_VER
                        or kaleido_ver >= self.KALEIDO_MAX_VER
                    ):
                        raise SettingsError("FIGURE_EXPORT_KALEIDO_VERSION")

                    export_width = export.get("width")
                    if export_width is not None:
                        if not isinstance(export_width, int) or export_width <= 0:
                            raise SettingsError("FIGURE_EXPORT_WIDTH_VALUE")
                    export_height = export.get("height")
                    if export_height is not None:
                        if not isinstance(export_height, int) or export_height <= 0:
                            raise SettingsError("FIGURE_EXPORT_HEIGHT_VALUE")

            show = figure_settings.get("show", False)
            if "show" in figure_settings and not isinstance(show, bool):
                raise SettingsError("FIGURE_SHOW_VALUE")

    # % -----------------------------
    # construction heuristic methods
    def _check_fitting(self, W, L, Xo, Yo, w, l, container_coords) -> bool:
        if Xo + w > W or Yo + l > L:
            return False

        for x in range(Xo, Xo + w):
            for y in range(Yo, Yo + l):
                if container_coords[y][x] == 1:
                    return False
        return True

    def _generate_points(
        self, container, segments, potential_points, A, B, debug
    ) -> None:
        Xo, Ay = A
        Bx, Yo = B
        horizontals, verticals = segments
        # EXTRA DEBBUGING
        # if debug:
        #     logger.debug("horizontals")
        #     for Y_level in horizontals:
        #         logger.debug(f"{Y_level} : {horizontals[Y_level]}")
        #     logger.debug("verticals")
        #     for X_level in verticals:
        #         print(f"{X_level} : {verticals[X_level]}")
        hors = sorted(horizontals)
        verts = sorted(verticals)
        L, W = container["L"], container["W"]
        if debug:
            logger.debug(f"\tverts ={verts}")
            logger.debug(f"\thors ={hors}")

        A_gen = 0
        append_A__ = True
        prohibit_A__and_E = False

        # A POINT ON BIN WALL
        if Ay < L and Xo == 0:
            A_gen = 1
            if debug:
                logger.debug(f"\tgen point A --> {A}")
            potential_points["A"].append(A)

        # A POINT NOT ON BIN WALL
        elif Ay < L:
            segments = verticals[Xo]
            append_A = False
            # checking vertical lines on Xo for potential A
            for seg in segments:
                if seg[0][1] == Ay or Ay == seg[1][1]:
                    # if vertical segment on Ay's X coord obstructs A
                    # prohibit A', E
                    prohibit_A__and_E = True
                if seg[0][1] <= Ay and seg[1][1] > Ay:
                    # if vertical segment on Ay's X coord passes through A
                    # or it's start touches A
                    append_A = True
                    break
            # if horizontal segment passes through A, prohibit A, A', E
            if Ay in hors:
                segments = horizontals[Ay]
                for seg in segments:
                    if seg[0][0] <= Xo and seg[1][0] > Xo:
                        append_A = False
                        append_A__ = False
                        break
            if append_A:
                if debug:
                    logger.debug(f"\tgen point A --> {A}")
                potential_points["A"].append(A)
                A_gen = True

        # A' or E POINT
        verts__lt__Xo = [x for x in verts if x < Xo]
        if not A_gen and not prohibit_A__and_E and verts__lt__Xo != []:
            num = 0
            stop = False
            found = False
            if debug:
                logger.debug(f"\n\tSEARCHING A' POINT. Ai=({Xo},{Ay})")
            for vert_X in verts__lt__Xo[-1::-1]:
                increased_num = False
                segments = verticals.get(vert_X, [])
                segments.sort()
                if debug:
                    logger.debug(f"\tvert_X = {vert_X}, \n\t\tsegments = {segments}")
                for seg in segments:
                    seg_start_Y, seg_end_Y, seg_start_X = seg[0][1], seg[1][1], seg[0][0]
                    # the verticals on this X have passed Ay landing point
                    # abort searching A'
                    if seg_start_Y > Ay:
                        if debug:
                            logger.debug("\t\tbreaking due to overpassed Ay")
                        break
                    # if segment with Y == Ay, check if it is continued
                    # if segment is discontinued, abort searching for A'
                    if seg_end_Y == Ay:
                        seg_index = segments.index(seg)
                        segs_to_search = segments[seg_index + 1 : :]
                        dont_stop = False
                        for sub_seg in segs_to_search:
                            if sub_seg[0][1] == Ay:
                                if debug:
                                    logger.debug("\t\tfound continuous corner segments")
                                dont_stop = True
                                break
                        if not dont_stop:
                            stop = True
                            if debug:
                                logger.debug(
                                    "\t\tbreaking due to non continuous obstacle"
                                )
                            break
                    # intersegments number
                    if not increased_num and (seg_end_Y > Yo and seg_end_Y < Ay):
                        num += 1
                        increased_num = True
                        if debug:
                            logger.debug(f"\t\tintersegment num = {num}")
                    # landing segment condition for A' appendance
                    if seg_start_Y <= Ay and seg_end_Y > Ay:
                        appendance_point = (seg_start_X, Ay)
                        if num <= 1 or (num <= 2 and increased_num):
                            if debug:
                                logger.debug(f"\t\tgen point A' --> {appendance_point}")
                            potential_points["A_"].append(appendance_point)
                        else:
                            if debug:
                                logger.debug(f"\t\tgen point E --> {appendance_point}")
                            potential_points["E"].append(appendance_point)
                        found = True
                if stop or found:
                    break

        # A'' POINT
        if not A_gen and Ay < L and append_A__:
            if debug:
                logger.debug(f"\tgen point A'' --> {A}")
            potential_points["A__"].append(A)

        # % ---------------------------------------------------------
        # % ---------------------------------------------------------
        B_gen = False
        prohibit_B__and_F = False
        append_B__ = True

        # B POINT ON BIN BOTTOM
        if Bx < W and Yo == 0:
            B_gen = True
            if debug:
                logger.debug(f"\tgen point B --> {B}")
            potential_points["B"].append(B)

        # B POINT NOT ON BIN BOTTOM
        elif Bx < W:
            segments = horizontals[Yo]
            append_B = False
            for seg in segments:
                if seg[0][0] == Bx or seg[1][0] == Bx:
                    # if horizontal segment on Bx's level obstructs B
                    # prohibit B', F
                    prohibit_B__and_F = 1
                if seg[0][0] <= Bx and seg[1][0] > Bx:
                    # if horizontal segment on Bx's level passes through B
                    append_B = True
                    break
            # check if vertical segment through B prohibits placement
            if Bx in verts:
                for seg in verticals[Bx]:
                    if seg[0][1] <= Yo and seg[1][1] > Yo:
                        append_B = False
                        append_B__ = False
                        break
            if append_B:
                B_gen = True
                if debug:
                    logger.debug(f"\tgen point B --> {B}")
                potential_points["B"].append(B)

        # B', F POINTS
        hors__lt__Yo = [y for y in hors if y < Yo]
        if not B_gen and not prohibit_B__and_F and hors__lt__Yo != []:
            num = 0
            stop = False
            found = False
            if debug:
                logger.debug(f"\n\tSEARCHING B' POINT. Bi=({Bx},{Yo})")
            for hor_Y in hors__lt__Yo[-1::-1]:
                increased_num = False
                segments = horizontals.get(hor_Y, [])
                segments.sort()
                if debug:
                    logger.debug(f"\thor_Y = {hor_Y}, \n\t\tsegments = {segments}")
                for seg in segments:
                    seg_start_X, seg_end_X, seg_start_Y = seg[0][0], seg[1][0], seg[0][1]
                    # the horizontals on this Y have passed Bx landing point
                    if seg_start_X > Bx:
                        if debug:
                            logger.debug("\t\tbreaking due to overpassed Ay")
                        break
                    if seg_end_X == Bx:
                        seg_index = segments.index(seg)
                        segs_to_serch = segments[seg_index + 1 : :]
                        dont_stop = False
                        for sub_seg in segs_to_serch:
                            if sub_seg[0][0] == Bx:
                                if debug:
                                    logger.debug("\t\tfound continuous corner segments")
                                dont_stop = True
                                break
                        if not dont_stop:
                            stop = True
                            if debug:
                                logger.debug(
                                    "\t\tbreaking due to non continuous obstacle"
                                )
                            break
                    # intersegments number
                    if not increased_num and (seg_end_X > Xo and seg_end_X < Bx):
                        num += 1
                        increased_num = True
                        if debug:
                            logger.debug(f"\t\tintersegment num = {num}")
                    # landing segment condition
                    if seg_start_X <= Bx and seg_end_X > Bx:
                        appendance_point = (Bx, seg_start_Y)
                        if num <= 1 or (num <= 2 and increased_num):
                            if debug:
                                logger.debug(f"\tgen point B' --> {appendance_point}")
                            potential_points["B_"].append(appendance_point)
                        else:
                            if debug:
                                logger.debug(f"\tgen point F --> {appendance_point}")
                            potential_points["F"].append(appendance_point)
                        found = True
                        break
                if stop or found:
                    break

        # B'' POINT
        # it is a marginally B point
        if not B_gen and Bx < W and append_B__:
            if debug:
                logger.debug(f"\tgen point B'' --> {B}")
            potential_points["B__"].append(B)

        # % ---------------------------------------------------------
        # C POINT
        if Ay in hors:
            segments = horizontals[Ay]
            append_C = False
            seg_end_X_to_append = None
            segments.sort()
            for seg in segments:
                seg_start_X = seg[0][0]
                seg_end_X = seg[1][0]
                # check if another segment follows
                if seg_end_X_to_append and seg_start_X == seg_end_X_to_append:
                    append_C = False
                    break
                if seg_end_X > Xo and seg_end_X < Bx:
                    append_C = True
                    seg_end_X_to_append = seg_end_X
            if append_C:
                if debug:
                    logger.debug(f"\tgen point C --> {(seg_end_X_to_append, Ay)}")
                potential_points["C"].append((seg_end_X_to_append, Ay))
                try:
                    potential_points["B__"].remove((seg_end_X_to_append, Ay))
                except ValueError:
                    pass

        # % ---------------------------------------------------------
        # D POINT:
        if Bx in verts:
            segments = verticals[Bx]
            append_D = False
            end_of_seg_Y_to_append = None
            for seg in segments:
                seg_end_Y = seg[1][1]
                seg_start_Y = seg[0][1]
                if seg_end_Y > Yo and seg_end_Y < Ay:
                    append_D = True
                    end_of_seg_Y_to_append = seg_end_Y
                if seg_start_Y < Ay and seg_end_Y > Ay:
                    append_D = False
                    break

            if append_D:
                if debug:
                    logger.debug(f"\tgen point D --> {(Bx, end_of_seg_Y_to_append)}")
                potential_points["D"].append((Bx, end_of_seg_Y_to_append))
                try:
                    potential_points["A__"].remove((Bx, end_of_seg_Y_to_append))
                except ValueError:
                    pass

    def _get_current_point(self, potential_points) -> tuple:
        for pclass in self._potential_points_strategy:
            if potential_points[pclass] != []:
                current_point = potential_points[pclass].pop(0)
                return current_point, pclass

        return (None, None)

    def _append_segments(self, segments, A, B, w, l) -> None:
        Xo, Ay = A
        Bx, Yo = B
        horizontals, verticals = segments
        horizontals_ = [((Xo, Yo), (Bx, Yo)), ((Xo, Ay), (Bx, Ay))]
        verticals_ = [((Xo, Yo), (Xo, Ay)), ((Bx, Yo), (Bx, Ay))]
        if Xo in verticals:
            verticals[Xo].append(verticals_[0])
        else:
            verticals[Xo] = [verticals_[0]]

        if Xo + w in verticals:
            verticals[Xo + w].append(verticals_[1])
        else:
            verticals[Xo + w] = [verticals_[1]]

        # APPEND HORIZONTAL SIDES IN horizontals
        if Yo in horizontals:
            horizontals[Yo].append(horizontals_[0])
        else:
            horizontals[Yo] = [horizontals_[0]]

        if Yo + l in horizontals:
            horizontals[Yo + l].append(horizontals_[1])
        else:
            horizontals[Yo + l] = [horizontals_[1]]

    def _construct(self, container, items, debug=False) -> tuple:
        """
        Point generation construction heuristic
        for solving single container problem instance.
        Input:
            container,
            items,
            debug (mode),
            implicitly by attribute, the potential points strategy
        Output:
            A. updates self.current_solution with the solution of the container.
            B. returns (remaining non-fitted items, containers utilization) tuple.
        """
        self.current_solution = {}
        # 'items' are the available for placement
        # after an item get's picked, it is erased
        items_ids = [_id for _id in items]
        W, L = container["W"], container["L"]
        total_surface = W * L
        # obj_value is the container utilization
        # obj_value = Area(Placed Items)/Area(Container)
        obj_value = 0
        container_coords = [[0 for x in range(W)] for y in range(L)]

        # set starting lines
        # lines = [horizontals, verticals]
        segments = [
            {  # horizontals
                0: [
                    ((0, 0), (W, 0)),
                ],
                L: [((0, L), (W, L))],
            },
            {  # verticals
                0: [
                    ((0, 0), (0, L)),
                ],
                W: [((W, 0), (W, L))],
            },
        ]
        potential_points = {
            "O": (0, 0),
            "A": [],
            "B": [],
            "A_": [],
            "B_": [],
            "A__": [],
            "B__": [],
            "C": [],
            "D": [],
            "E": [],
            "F": [],
        }

        # O(0, 0) init point
        current_point, point_class = potential_points["O"], "O"

        while True:
            if current_point is None or items == {} or obj_value >= 0.999999:
                break

            if debug:
                logger.debug(f"\nCURRENT POINT: {current_point} class: {point_class}")
                # container_str = []
                # for y in range(L):
                #     s = " ".join([str(x_y) for x_y in [point for x in range(W) for point in container_coords[x]] ])
                #     container_str.append(s)
                # print("\n".join(container_str))

            Xo, Yo = current_point

            # CURRENT POINT'S ITEM SEARCH
            for item_id in items_ids:
                item = items[item_id]
                w, l, rotated = item["w"], item["l"], False

                check = self._check_fitting(W, L, Xo, Yo, w, l, container_coords)
                if not check:
                    if self._rotation:
                        rotated = True
                        w, l = l, w
                        check = self._check_fitting(W, L, Xo, Yo, w, l, container_coords)
                        if not check:
                            continue
                    else:
                        continue

                if debug:
                    logger.debug(f"--> {item_id}\n")

                # add item to container
                for x in range(Xo, Xo + w):
                    for y in range(Yo, Yo + l):
                        container_coords[y][x] = 1

                # removing item wont affect execution. 'for' breaks below
                items_ids.remove(item_id)
                del items[item_id]

                obj_value += w * l / total_surface

                item.update({"Xo": Xo, "Yo": Yo, "rotated": rotated})
                self.current_solution[item_id] = item

                A, B = (Xo, Yo + l), (Xo + w, Yo)
                self._generate_points(container, segments, potential_points, A, B, debug)
                self._append_segments(segments, A, B, w, l)
                break

            if debug:
                self._current_potential_points = deepcopy(potential_points)
            current_point, point_class = self._get_current_point(potential_points)

        return items, obj_value

    # % -----------------------------

    def _get_current_solution(self):
        """
        Returns the solution object, if there was a solution convergence.
        """
        solution = {}
        for _id in self.current_solution:
            l = self.current_solution[_id]["l"]
            w = self.current_solution[_id]["w"]
            Xo = self.current_solution[_id]["Xo"]
            Yo = self.current_solution[_id]["Yo"]
            if self.current_solution[_id]["rotated"]:
                l, w = w, l
            solution[_id] = [Xo, Yo, w, l]
        return solution

    def solve(self, items_sequence=None, debug=False) -> None:
        """
        Solves for all the containers, using the
        `point generation construction heuristic <https://github.com/AlkiviadisAleiferis/hyperpack-theory/>`_.

        **OPERATION**
            - Populates ``self.solution`` with solution found for every container.
            - Populates ``self.obj_val_per_container`` with the utilization of every container.

        **PARAMETERS**
            - ``items_sequence`` : the sequence of ids to create the items to solve for. \
            If None, ``self.items`` will be used. Items used for solving are deepcopied \
            from self.items with corresponding sequence.

            - ``debug`` : If True, debuging mode will be enabled, usefull \
            only for developing.

        **RETURNS**
            ``None``

        **NOTES**
            Solution is deterministic, and solely dependent on these factors:

            - ``potential_points_strategy`` attribute for the potential points strategy.
            - ``items_sequence`` **sequence** of the items ids.
        """
        # deepcopying is done cause items will be removed
        # from items pool after each container is solved
        # self._items shouldn't have same id with items
        if items_sequence is None:
            items = self._items.deepcopy()
        else:
            items = self._items.deepcopy(items_sequence)

        self.obj_val_per_container = {}
        self.solution = {}

        for container_id, container in self._containers.items():
            self.solution[container_id] = {}
            self.obj_val_per_container[container_id] = 0
            if items == {}:
                continue
            items, util = self._construct(container=container, items=items, debug=debug)
            self.obj_val_per_container[container_id] = util
            self.solution[container_id] = self._get_current_solution()

    # % -----------------------------
    # figure methods
    def colorgen(self, index) -> str:
        return constants.ITEMS_COLORS[index]

    def get_figure_dtick_value(self, dimension, scale=20):
        return math.ceil(dimension / scale)

    def create_figure(self, show=False) -> None:
        """
        Method used for creating figures and showing/exporting them.

        **OPERATION**
            Create's the solution's figure.

        **PARAMETERS**
            - ``show``: if True, the created figure will be displayed in browser \
            after creation.

        **WARNING**
            plotly library at least 5.10.4 must be installed in environment,
            and for image exportation, at least kaleido 0.2.1. See :ref:`here<figures_guide>` for
            detailed explanation of the method.
        """

        if not self.solution:
            hyperLogger.warning(FigureExportError.NO_SOLUTION_WARNING)
            return

        try:
            import plotly.graph_objects as go
        except ImportError:
            raise SettingsError("PLOTLY_NOT_INSTALLED")

        figure_settings = self._settings.get("figure", {})
        export = figure_settings.get("export")
        show = figure_settings.get("show") or show

        containers_ids = tuple(self._containers)

        for cont_id in containers_ids:
            fig = go.Figure()
            fig.add_annotation(
                text=cont_id,
                showarrow=False,
                xref="x domain",
                yref="y domain",
                # The arrow head will be 25% along the x axis, starting from the left
                x=0.5,
                # The arrow head will be 40% along the y axis, starting from the bottom
                y=1,
                font={"size": 20},
            )
            L = self._containers[cont_id]["L"]
            W = self._containers[cont_id]["W"]
            fig.update_xaxes(
                range=[-2, W + 2],
                tick0=0,
                dtick=self.get_figure_dtick_value(W),
                zeroline=True,
                zerolinewidth=1,
            )
            fig.update_yaxes(
                range=[-2, L + 2],
                scaleanchor="x",
                scaleratio=1,
                tick0=0,
                dtick=self.get_figure_dtick_value(L),
                zeroline=True,
                zerolinewidth=1,
            )
            for i, item_id in enumerate(self.solution[cont_id]):
                Xo = self.solution[cont_id][item_id][0]
                Yo = self.solution[cont_id][item_id][1]
                w = self.solution[cont_id][item_id][2]
                l = self.solution[cont_id][item_id][3]
                shape_color = self.colorgen(i)
                fig.add_shape(
                    type="rect",
                    x0=Xo,
                    y0=Yo,
                    x1=Xo + w,
                    y1=Yo + l,
                    line=dict(color="black"),
                    fillcolor=shape_color,
                    label={"text": item_id, "font": {"color": "white", "size": 12}},
                )
                fig.add_trace(
                    go.Scatter(
                        x=[Xo, Xo + w, Xo + w, Xo],
                        y=[Yo, Yo, Yo + l, Yo + l],
                        showlegend=False,
                        hoverinfo="x+y",
                    )
                )

            fig.add_shape(
                type="rect",
                x0=0,
                y0=0,
                x1=W,
                y1=L,
                line=dict(
                    color="Black",
                    width=2,
                ),
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

    # % -----------------------------

    def _deepcopy_items(self, items=None):
        if items is None:
            items = self._items
        return {_id: {key: items[_id][key] for key in items[_id]} for _id in items}

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

    def orient_items(self, orientation: str or None = "wide") -> None:
        """
        Method for orienting the ``items`` structure.

        **OPERATION**
            Orients each item in items set by rotating it
            (interchange w, l of item). See :ref:`here<orient_items>` for
            detailed explanation of the method.

        **PARAMETERS**
            ``orientation`` : "wide"/"long". If None provided, orientation will be skipped.

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

        if orientation not in ("wide", "long"):
            hyperLogger.warning(
                f"orientation parameter '{orientation}' not valid. Orientation skipped."
            )
            return

        for _id in items:
            w, l = items[_id]["w"], items[_id]["l"]

            if orientation == "wide" and l > w:
                items[_id]["w"], items[_id]["l"] = l, w

            elif orientation == "long" and l < w:
                items[_id]["w"], items[_id]["l"] = l, w

    def sort_items(self, sorting_by: tuple or None = ("area", True)) -> None:
        """
        Method for ordering the ``items`` structure. See :ref:`here<sort_items>` for
        detailed explanation of the method.

        **OPERATION**
            Sorts the ``self.items`` according to ``sorting_by`` parameter guidelines.

        **PARAMETERS**
            ``sorting_by`` : (sorting criterion, reverse). If None provided, sorting will be skipped.

        **WARNING**
            Changing the values of ``self.items`` causes resetting of the ``solution`` attribute.

        **RETURNS**
            ``None``
        """
        if sorting_by is None:
            return

        by, reverse = sorting_by

        items = self._items.deepcopy()

        if by == "area":
            sorted_items = [[i["w"] * i["l"], _id] for _id, i in items.items()]
            sorted_items.sort(reverse=reverse)
        elif by == "perimeter":
            sorted_items = [[i["w"] * 2 + i["l"] * 2, _id] for _id, i in items.items()]
            sorted_items.sort(reverse=reverse)
        elif by == "longest_side_ratio":
            sorted_items = [
                [max(i["w"], i["l"]) / min(i["w"], i["l"]), _id]
                for _id, i in items.items()
            ]
            sorted_items.sort(reverse=reverse)
        else:
            raise NotImplementedError

        self.items = {el[1]: items[el[1]] for el in sorted_items}

    def _calc_obj_value(self):
        """
        Calculates the objective value
        using 'obj_val_per_container' attribute.
        Returns a float (total utilization).
        In case more than 1 bin is used, last bun's
        utilization is reduced to push first bin's
        maximum utilization.
        """
        containers_obj_vals = tuple(self.obj_val_per_container.values())
        if self._containers_num == 1:
            return sum([u for u in containers_obj_vals])
        else:
            return (
                sum([u for u in containers_obj_vals[:-1]])
                + 0.7 * containers_obj_vals[-1]
            )

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, value):
        self._items = Items(value, self)

    @items.deleter
    def items(self):
        raise ItemsError("CANT_DELETE")

    @property
    def containers(self):
        return self._containers

    @containers.setter
    def containers(self, value):
        self._containers = Containers(value, self)
        self._containers_num = len(value)

    @containers.deleter
    def containers(self):
        raise ContainersError("CANT_DELETE")

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, value):
        self._settings = value
        self.validate_settings()

    @settings.deleter
    def settings(self):
        raise SettingsError("CANT_DELETE_SETTINGS")

    @property
    def potential_points_strategy(self):
        return self._potential_points_strategy

    @potential_points_strategy.setter
    def potential_points_strategy(self, value):
        if not isinstance(value, tuple):
            raise PotentialPointsError("TYPE")

        checked_elements = set()
        for el in value:
            if not isinstance(el, str):
                raise PotentialPointsError("ELEMENT_TYPE")

            if el not in self.DEFAULT_POTENTIAL_POINTS_STRATEGY:
                raise PotentialPointsError("ELEMENT_NOT_POINT")

            if el in checked_elements:
                raise PotentialPointsError("DUPLICATE_POINTS")
            checked_elements.add(el)

        self._potential_points_strategy = value

    @potential_points_strategy.deleter
    def potential_points_strategy(self):
        raise PotentialPointsError("DELETE")


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
        _force_raise_error_index=None,
    ):
        super().__init__()
        self.throttle = throttle
        self._force_raise_error_index = _force_raise_error_index
        self.index = index
        self.shared_array = shared_array
        self.queue = Queue()
        self.strategies_chunk = strategies_chunk
        if settings.get("workers_num", 1) > 1:
            settings["workers_num"] = 1
        self.hyper_instance = HyperPack(
            containers=containers, items=items, settings=settings
        )
        self.hyper_instance.start_time = start_time
        # it is the processe' name
        self.name = name

    def run(self):
        try:
            if self._force_raise_error_index in (self.index, "all"):
                raise MultiProcessError("testing error")
            self.hyper_instance.solve(debug=False)
            best_obj_val = self.hyper_instance._calc_obj_value()
            best_solution = self.hyper_instance._deepcopy_solution()
            best_obj_val_per_container = (
                self.hyper_instance._copy_objective_val_per_container()
            )
            best_strategy = None
            max_obj_value = (
                self.hyper_instance._containers_num - 0.3
                if self.hyper_instance._containers_num != 1
                else 1
            )
            for potential_points_strategy in self.strategies_chunk:
                # set the construction's heuristic potential points strategy
                # to the current sequence of the search
                self.hyper_instance._potential_points_strategy = (
                    potential_points_strategy
                )
                self.hyper_instance.local_search(
                    throttle=self.throttle, _hypersearch=True
                )
                new_obj_val = self.hyper_instance._calc_obj_value()
                if new_obj_val > self.shared_array[self.index]:
                    best_obj_val_per_container = (
                        self.hyper_instance._copy_objective_val_per_container()
                    )
                    best_obj_val = self.hyper_instance._calc_obj_value()
                    best_solution = self.hyper_instance._deepcopy_solution()
                    best_strategy = [point for point in potential_points_strategy]
                    self.shared_array[self.index] = new_obj_val
                    if new_obj_val >= max(self.shared_array):
                        hyperLogger.debug(
                            f"\t--Process {self.name} --> New best solution: {new_obj_val}\n"
                        )
                    if best_obj_val > max_obj_value - 0.0001:
                        hyperLogger.debug(
                            f"Process {self.name} acquired MAX objective value"
                        )
                        break

                if (
                    time.time() - self.hyper_instance.start_time
                    > self.hyper_instance._max_time_in_seconds
                ) or max(self.shared_array) >= max_obj_value - 0.001:
                    hyperLogger.debug(
                        f"Process {self.name}--> Exiting due to surpassed max time or max reached value"
                    )
                    break

            self.queue.put(
                (best_obj_val, best_solution, best_obj_val_per_container, best_strategy)
            )

        except Exception as e:
            hyperLogger.error(f"Process {self.name} failed with error: {str(e)}")
            self.shared_array[self.index] = -1
            self.queue.put((-1, {}, {}, None))


class HyperPack(PointGenPack):
    """
    This class extends ``PointGenPack``, utilizing it's solving functionalities
    by implementing:

        **A.** a hill-climbing, 2-opt exchange local search

        **B.** a hypersearch hyper-heuristic.
    """

    # Potential points strategies constant suffix
    STRATEGIES_SUFFIX = ("A__", "B__", "F", "E")
    # max neighbors parsing per node for large instances
    MAX_NEIGHBORS_THROTTLE = 2500

    def get_strategies(self, *, _exhaustive: bool = True) -> tuple:
        """
        Returns the potential points strategies to be treversed in hypersearch.
        """
        if _exhaustive:
            return [
                x + self.STRATEGIES_SUFFIX
                for x in list(permutations(["A", "B", "C", "D", "A_", "B_"], 6))
            ]
        else:
            # for testing or customization purposes
            return constants.DEFAULT_POTENTIAL_POINTS_STRATEGY_POOL

    def _single_process_hypersearch(self, strategies: tuple, throttle: bool):
        hyperLogger.debug("Solving with single core")
        # get first solution for comparison
        self.solve(debug=False)
        best_obj_val = self._calc_obj_value()
        best_solution = self._deepcopy_solution()
        best_obj_val_per_container = self._copy_objective_val_per_container()
        best_strategy = self.DEFAULT_POTENTIAL_POINTS_STRATEGY

        max_obj_value = self._containers_num - 0.3 if self._containers_num != 1 else 1

        for potential_points_strategy in strategies:
            # set the construction heuristic's potential points strategy
            # to the current strategy of the search
            # used in '_get_current_point' method
            self._potential_points_strategy = potential_points_strategy
            self.local_search(throttle=throttle, _hypersearch=True)
            # local search has updated self.solution
            # and self.obj_val_per_container
            new_obj_val = self._calc_obj_value()
            if new_obj_val > best_obj_val:
                # retain best found in memory
                best_obj_val_per_container = self._copy_objective_val_per_container()
                best_obj_val = new_obj_val
                best_solution = self._deepcopy_solution()
                best_strategy = [point for point in potential_points_strategy]
                hyperLogger.debug(f"\tNew best solution: {best_obj_val}\n")
            if new_obj_val >= max_obj_value - 0.0001:
                hyperLogger.debug("Terminating due to max objective value obtained")
                break
            if time.time() - self.start_time > self._max_time_in_seconds:
                hyperLogger.debug("Terminating due to surpassed max time")
                break

        return (best_solution, best_obj_val_per_container, best_strategy)

    def _multi_process_hypersearch(
        self, strategies: tuple, throttle: bool, _force_raise_error_index
    ):
        strategies_per_process = math.ceil(len(strategies) / self._workers_num)
        strategies_chunks = [
            strategies[i : i + strategies_per_process]
            for i in range(0, len(strategies), strategies_per_process)
        ]

        processes = []
        shared_Array = Array("d", [0] * len(strategies_chunks))

        for i, strategies_chunk in enumerate(strategies_chunks):
            processes.append(
                HyperSearchProcess(
                    index=i,
                    containers=self._containers.deepcopy(),
                    items=self.items.deepcopy(),
                    settings=self._settings,
                    strategies_chunk=strategies_chunk,
                    name=f"hypersearch_{i}",
                    start_time=self.start_time,
                    shared_array=shared_Array,
                    throttle=throttle,
                    _force_raise_error_index=_force_raise_error_index,
                )
            )
        for p in processes:
            p.start()
        for p in processes:
            p.join()
        # at this point the processes concluded operation
        # get winning process and update instance data
        shared_list = list(shared_Array)

        # check if all/some processes failed
        if max(shared_list) == -1:
            raise MultiProcessError("ALL_PROCESSES_FAILED")
        elif -1 in shared_list:
            hyperLogger.error(
                "Some of the processes raised an exception. Please check logs."
            )

        win_process_index = shared_list.index(max(shared_list))
        win_process = processes[win_process_index]
        win_metrics = win_process.queue.get()
        hyperLogger.debug(f"\nWinning Process {win_process.name} found max")
        hyperLogger.debug(f"\tobj_val = {win_metrics[0]}")
        hyperLogger.debug(f"\tsequence = {win_metrics[3]}")
        best_solution = self._deepcopy_solution(win_metrics[1])
        best_obj_val_per_container = self._copy_objective_val_per_container(
            win_metrics[2]
        )
        if win_metrics[3] is None:
            best_strategy = None
        else:
            best_strategy = [point for point in win_metrics[3]]
        win_process.queue.close()

        # Log rest of the processes
        # UNCOMMENT FOR EXTRA DEBUGGING ON PROCESSES
        # for p_index, p in enumerate(processes):
        #     if p_index == win_proc_index:
        #         continue
        #     metrics = p.queue.get()
        #     hyperLogger.debug(f"\nProcess '{p.name}' complete")
        #     hyperLogger.debug(f"\tobj_val = {metrics[0]}")
        #     hyperLogger.debug(f"\tsequence = {metrics[3]}")
        #     p.queue.close()

        return (best_solution, best_obj_val_per_container, best_strategy)

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

            ``_hypersearch``: Either standalone (False), or part of a superset search (used by hypersearch).

            ``debug``: for developing debugging.

        **RETURNS**
            ``None``
        """

        # if not deployed by hypersearch
        # set default points sequence
        if not _hypersearch:
            self.start_time = time.time()
        else:
            hyperLogger.debug(
                f"\t\tCURRENT POTENTIAL POINTS STRATEGY: {self._potential_points_strategy}"
            )

        # INIT BEST SOLUTION s*
        self.solve(debug=False)
        # deepcopying solution
        best_solution = self._deepcopy_solution()
        best_obj_val_per_container = self._copy_objective_val_per_container()
        best_obj_value = self._calc_obj_value()

        max_obj_value = self._containers_num - 0.3 if self._containers_num != 1 else 1

        # INIT NEIGHBORHOOD
        # node_seq is the original sequence (node),
        # from which all the neighbors/next nodes are produced
        node_seq = list(self._items)
        items_num = len(self._items)

        node_num = 1
        continue_criterion = True

        max_neighbors_num = items_num * (items_num - 1) / 2
        if throttle and max_neighbors_num > self.MAX_NEIGHBORS_THROTTLE:
            max_neighbors_num = self.MAX_NEIGHBORS_THROTTLE

        while continue_criterion:
            node_num += 1
            out_of_time = False
            neighbor_found, processed_neighbors = (False, 0)
            global_optima = False
            break_ = False
            # begin neighborhood search
            for i in range(items_num):
                for j in range(i + 1, items_num):
                    current_seq = [item_id for item_id in node_seq]
                    current_seq[i], current_seq[j] = current_seq[j], current_seq[i]

                    self.solve(items_sequence=current_seq, debug=False)
                    new_obj_value = self._calc_obj_value()
                    processed_neighbors += 1

                    if new_obj_value > best_obj_value:
                        if debug:
                            hyperLogger.debug("-- new node found")
                        # deepcopying solution
                        best_obj_value = new_obj_value
                        best_obj_val_per_container = (
                            self._copy_objective_val_per_container()
                        )
                        best_solution = self._deepcopy_solution()

                        # set new node
                        node_seq = [item_id for item_id in current_seq]

                        neighbor_found = True
                        global_optima = best_obj_value >= max_obj_value - 0.0001

                    out_of_time = (
                        time.time() - self.start_time >= self._max_time_in_seconds
                    )
                    max_neighbors = processed_neighbors >= max_neighbors_num

                    break_ = (
                        out_of_time or neighbor_found or global_optima or max_neighbors
                    )
                    if break_:
                        break

                if break_:
                    break

            # no improving neighbor found in neighborhood
            # or out of time
            # or global_optima
            # local search terminates
            if debug:
                hyperLogger.debug(f"\tnode num: {node_num}")
                hyperLogger.debug(f"\tbest obj_val: {best_obj_value}")
                hyperLogger.debug(f"\tprocessed_neighbors : {processed_neighbors}\n")
                if out_of_time:
                    hyperLogger.debug("-- out of time - exiting")
                elif not neighbor_found:
                    hyperLogger.debug("-- no new node found - local optima - exiting")
                elif global_optima:
                    hyperLogger.debug("-- global optimum found - exiting")

            # update continue criterion
            continue_criterion = neighbor_found and not out_of_time and not global_optima

        # after local search has ended, restore optimum values
        self.obj_val_per_container = best_obj_val_per_container
        self.solution = best_solution

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
            Solves using ``local_search`` for different ``potential_points_strategy`` values.

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

            ``throttle`` boolean **(keyword only)** passed to local search. Affects large instances of the problem.

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

        hyperLogger.info("Initiating Hypersearch.")

        best_solution, best_obj_val_per_container, best_strategy = (
            self._single_process_hypersearch(strategies, throttle)
            if self._workers_num == 1
            else self._multi_process_hypersearch(
                strategies, throttle, _force_raise_error_index
            )
        )

        hyperLogger.info("Hypersearch terminates.")

        # SET BEST SOLUTION
        self.solution = best_solution
        self.obj_val_per_container = best_obj_val_per_container
        self.best_strategy = best_strategy

        total_time = time.time() - self.start_time
        hyperLogger.debug(f"Execution time : {total_time} [sec]")

    def log_solution(self) -> str:
        """
        Logs the solution.

        If a solution isn't available a proper message is displayed.
        """
        if not getattr(self, "solution", False):
            hyperLogger.warning("No solving operation has been concluded.")
            return

        log = ["\nSOLUTION LOG:"]
        percent_items_stored = sum(
            [len(i) for cont_id, i in self.solution.items()]
        ) / len(self._items)
        log.append(f"Percent total items stored : {percent_items_stored*100:.4f}%")
        for cont_id in self._containers:
            W, L = self._containers[cont_id]["W"], self._containers[cont_id]["L"]
            log.append(f"Container: {cont_id} {W}x{L}")
            total_items_area = sum(
                [i[2] * i[3] for item_id, i in self.solution[cont_id].items()]
            )
            log.append(f"\t[util%] : {total_items_area*100/(W*L):.4f}%")
        items_ids = {_id for cont_id, items in self.solution.items() for _id in items}
        remaining_items = [_id for _id in self._items if _id not in items_ids]
        log.append(f"\nRemaining items : {remaining_items}")
        output_log = "\n".join(log)
        repr(output_log)
        hyperLogger.info(output_log)
        return output_log
