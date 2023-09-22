import math
from operator import lt, gt, le, ge
import platform
import re
import sys
import time
from array import array
from collections import deque
from copy import deepcopy
from itertools import permutations, combinations
from multiprocessing import Array, Process, Queue, cpu_count, current_process
from pathlib import Path

from . import constants
from .abstract import AbstractLocalSearch
from .processes import HyperSearchProcess
from .exceptions import (
    ContainersError,
    FigureExportError,
    ItemsError,
    MultiProcessError,
    PotentialPointsError,
    SettingsError,
    DimensionsError,
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
    # defaults
    MAX_TIME_IN_SECONDS_DEFAULT_VALUE = 60
    WORKERS_NUM_DEFAULT_VALUE = 1
    ROTATION_DEFAULT_VALUE = True
    FIGURE_DEFAULT_FILE_NAME = "PlotlyGraph"
    MAX_W_L_RATIO = 10
    STRIP_PACK_INIT_HEIGHT = 2**100
    STRIP_PACK_CONT_ID = "strip-pack-container"
    # settings constraints
    FIGURE_FILE_NAME_REGEX = re.compile(r"[a-zA-Z0-9_-]{1,45}$")
    ACCEPTED_IMAGE_EXPORT_FORMATS = ("pdf", "png", "jpeg", "webp", "svg")
    PLOTLY_MIN_VER = ("5", "14", "0")
    PLOTLY_MAX_VER = ("6", "0", "0")
    KALEIDO_MIN_VER = ("0", "2", "1")
    KALEIDO_MAX_VER = ("0", "3", "0")

    # % --------------- initialization --------------
    def __init__(self, containers=None, items=None, settings=None, *, strip_pack_width=None):
        self._check_strip_pack(strip_pack_width)
        if not self._strip_pack:
            self._containers = Containers(containers, self)
        elif containers is not None:
            raise ContainersError("STRIP_PACK_ONLY")

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

                ``_get_container_height``: Branches method to return solution height \
                or a minimum.

            ``_container_height``: is the actual container's height used in ``_construct``. \
            Is also updated in every new node solution in local_search, where a lower \
            height is proven feasible.

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
            raise DimensionsError("DIMENSION_VALUE")

        self._strip_pack = True
        self._container_height = self.MAX_W_L_RATIO * strip_pack_width
        containers = {
            "strip-pack-container": {"W": strip_pack_width, "L": self.STRIP_PACK_INIT_HEIGHT}
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
            if not self._plotly_installed:
                raise SettingsError("PLOTLY_NOT_INSTALLED")

            if not self._plotly_ver_ok:
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
                    if not self._kaleido_installed:
                        raise SettingsError("FIGURE_EXPORT_KALEIDO_MISSING")

                    if not self._kaleido_ver_ok:
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

    # % --------- construction heuristic methods ----------

    def _check_fitting(self, W, L, Xo, Yo, w, l, container_coords) -> bool:
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

    def _generate_points(
        self, container, horizontals, verticals, potential_points, Xo, Yo, w, l, debug
    ) -> None:
        A, B, Ay, Bx = (Xo, Yo + l), (Xo + w, Yo), Yo + l, Xo + w
        # EXTRA DEBBUGING
        # if debug:
        #     logger.debug("horizontals")
        #     for Y_level in horizontals:
        #         logger.debug(f"{Y_level} : {horizontals[Y_level]}")
        #     logger.debug("verticals")
        #     for X_level in verticals:
        #         print(f"{X_level} : {verticals[X_level]}")
        hors, verts, L, W = (
            sorted(horizontals),
            sorted(verticals),
            container["L"],
            container["W"],
        )
        if debug:
            logger.debug(f"\tverts ={verts}\n\thors ={hors}")

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
                                logger.debug("\t\tbreaking due to non continuous obstacle")
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
                                logger.debug("\t\tbreaking due to non continuous obstacle")
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
            if potential_points[pclass]:
                return potential_points[pclass].popleft(), pclass

        return (None, None)

    def _append_segments(self, horizontals, verticals, Xo, Yo, w, l) -> None:
        # A, B = (Xo, Yo + l), (Xo + w, Yo)
        Ay, Bx = Yo + l, Xo + w

        # verticals -------------------------------
        if Xo in verticals:
            verticals[Xo].append(((Xo, Yo), (Xo, Ay)))
        else:
            verticals[Xo] = [((Xo, Yo), (Xo, Ay))]

        if Xo + w in verticals:
            verticals[Xo + w].append(((Bx, Yo), (Bx, Ay)))
        else:
            verticals[Xo + w] = [((Bx, Yo), (Bx, Ay))]

        # horizontals -------------------------------
        if Yo in horizontals:
            horizontals[Yo].append(((Xo, Yo), (Bx, Yo)))
        else:
            horizontals[Yo] = [((Xo, Yo), (Bx, Yo))]

        if Yo + l in horizontals:
            horizontals[Yo + l].append(((Xo, Ay), (Bx, Ay)))
        else:
            horizontals[Yo + l] = [((Xo, Ay), (Bx, Ay))]

    def _construct(self, cont_id, container, items, debug=False) -> tuple:
        """
        Point generation construction heuristic
        for solving single container problem instance.

        INPUT
            container,
            items,
            debug (mode),

            implicitly by attribute, the potential points strategy

        OUTPUT
            A. updates self.current_solution with the solution of the container.
            B. returns (remaining non-fitted items, containers utilization) tuple.
        """
        self.current_solution = {}
        strip_pack = self._strip_pack

        # 'items' are the available for placement
        # after an item get's picked, it is erased
        items_ids = [_id for _id in items]

        if strip_pack:
            L = self._container_height
        else:
            L = container["L"]
        W = container["W"]

        total_surface = W * L
        # obj_value is the container utilization
        # obj_value = Area(Placed Items)/Area(Container)
        obj_value = 0
        items_area = 0
        max_obj_value = 1

        container_coords = [array("I", [0] * W) for y in range(L)]

        # set starting lines
        horizontals = {0: [((0, 0), (W, 0))]}
        verticals = {0: [((0, 0), (0, L))], W: [((W, 0), (W, L))]}

        potential_points = {
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

        # O(0, 0) init point
        current_point, point_class = potential_points["O"], "O"

        # start of item placement process
        while True:
            if current_point is None or not items_ids or obj_value >= max_obj_value:
                break

            if debug:
                logger.debug(f"\nCURRENT POINT: {current_point} class: {point_class}")

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
                for y in range(Yo, Yo + l):
                    container_coords[y][Xo : Xo + w] = array("I", [1] * w)

                # removing item wont affect execution. 'for' breaks below
                items_ids.remove(item_id)
                del items[item_id]

                items_area += w * l
                obj_value += w * l / total_surface

                item.update({"Xo": Xo, "Yo": Yo, "rotated": rotated})
                self.current_solution[item_id] = item

                self._generate_points(
                    container,
                    horizontals,
                    verticals,
                    potential_points,
                    Xo,
                    Yo,
                    w,
                    l,
                    debug,
                )
                self._append_segments(horizontals, verticals, Xo, Yo, w, l)
                break

            if debug:
                self._current_potential_points = deepcopy(potential_points)
            current_point, point_class = self._get_current_point(potential_points)
        # end of item placement process

        if strip_pack:
            height_of_solution = max(set(horizontals)) or 1
            obj_value = items_area / (W * height_of_solution)

        return items, obj_value

    # % ------------------ solving ---------------------

    def _get_current_solution(self):
        """
        Returns the solution object of the _construct method
        for the current solving container.
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

    def solve(self, sequence=None, debug=False) -> None:
        """
        Solves for all the containers, using the
        `point generation construction heuristic
        <https://github.com/AlkiviadisAleiferis/hyperpack-theory/>`_.

        **OPERATION**
            Populates ``self.solution`` with solution found for every container.

            Populates ``self.obj_val_per_container`` with the utilization \
            of every container.

        **PARAMETERS**
            ``items_sequence`` : the sequence of ids to create the items to solve for. \
            If None, ``self.items`` will be used. Items used for solving are deepcopied \
            from self.items with corresponding sequence.

            ``debug`` : If True, debuging mode will be enabled, usefull \
            only for developing.

        **RETURNS**
            ``None``

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

        self.obj_val_per_container = {}
        self.solution = {}

        for cont_id in self._containers:
            self.solution[cont_id] = {}
            self.obj_val_per_container[cont_id] = 0
            if items == {}:
                continue
            items, util = self._construct(
                cont_id, container=self._containers[cont_id], items=items, debug=debug
            )
            self.obj_val_per_container[cont_id] = util
            self.solution[cont_id] = self._get_current_solution()

    # % -------------- figure methods ---------------

    def colorgen(self, index) -> str:
        """
        Method for returning a hexadecimal color for every item
        in the graph.
        """
        return constants.ITEMS_COLORS[index]

    def get_figure_dtick_value(self, dimension, scale=20):
        """
        Method for determining the distance between ticks in
        x or y dimension.
        """
        return math.ceil(dimension / scale)

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
            raise SettingsError("PLOTLY_NOT_INSTALLED")

        elif not self._plotly_ver_ok:
            raise SettingsError("PLOTLY_VERSION")
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
            fig = go.Figure()
            fig.add_annotation(
                text="Powered by Hyperpack",
                showarrow=False,
                xref="x domain",
                yref="y domain",
                # The arrow head will be 25% along the x axis, starting from the left
                x=0.5,
                # The arrow head will be 40% along the y axis, starting from the bottom
                y=1,
                font={"size": 25, "color": "white"},
            )
            fig.update_layout(
                title=dict(text=f"{cont_id}", font=dict(size=25)),
                xaxis_title="Container width (x)",
                yaxis_title="Container Length (y)",
            )

            L = self._get_container_height(cont_id)
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
                Xo, Yo, w, l = self.solution[cont_id][item_id]
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
                        fig.write_image(export_path / f"{file_name}__{cont_id}.{file_format}")

                except Exception as e:
                    error_msg = FigureExportError.FIGURE_EXPORT.format(e)
                    raise FigureExportError(error_msg)
            if show:
                fig.show(config={"responsive": False})

    # % ---------------- auxiliary methods ---------------------------------

    def _set_container_height(self):
        cont_id = self.STRIP_PACK_CONT_ID

        if not self.solution:
            height = self.containers[cont_id]["W"] * self.MAX_W_L_RATIO

        else:
            solution = self.solution[cont_id]
            # height of items stack in solution
            solution_height = max(
                [solution[item_id][1] + solution[item_id][3] for item_id in solution] or [0]
            )

            # preventing container height to drop below point
            if self._container_min_height is not None:
                height = max(solution_height, self._container_min_height)
            else:
                height = solution_height

        self._container_height = height

    def _get_container_height(self, cont_id="strip-pack-container"):
        """
        **Calculates and returns the container's height.**

        In case of bin-packing:
            it returns the containers height.

        In case of strip packing:
            if a solution has been found return
            ``_container_min_height`` OR
            height of items stack in solution

            if a solution has not been found, return
            (container Width)* ``self.MAX_W_L_RATIO``

        Used in:
            ``create_figure``

            ``log_solution``
        """
        if self._strip_pack:
            if not self.solution:
                return self.containers[cont_id]["W"] * self.MAX_W_L_RATIO

            else:
                solution = self.solution[cont_id]
                # height of items stack in solution
                solution_height = max(
                    [solution[item_id][1] + solution[item_id][3] for item_id in solution]
                    or [0]
                )

                # preventing container height to drop below point
                if self._container_min_height is not None:
                    return max(solution_height, self._container_min_height)

                return solution_height
        else:
            return self._containers[cont_id]["L"]

    def _deepcopy_items(self, items=None):
        if items is None:
            items = self._items
        return {_id: {key: items[_id][key] for key in items[_id]} for _id in items}

    def _copy_objective_val_per_container(self, obj_val_per_container=None):
        if obj_val_per_container is None:
            obj_val_per_container = self.obj_val_per_container
        return {cont_id: obj_val_per_container[cont_id] for cont_id in obj_val_per_container}

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
            (interchange w, l of item).

            See :ref:`here<orient_items>` for
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
            Sorts the ``self.items``

            according to ``sorting_by`` parameter guidelines.

        **PARAMETERS**
            ``sorting_by`` : (sorting criterion, reverse). If None provided, sorting
            will be skipped.

        **WARNING**
            Changing the values of ``self.items`` causes resetting of the
            ``solution`` attribute.

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
                [max(i["w"], i["l"]) / min(i["w"], i["l"]), _id] for _id, i in items.items()
            ]
            sorted_items.sort(reverse=reverse)
        else:
            raise NotImplementedError

        self.items = {el[1]: items[el[1]] for el in sorted_items}

    def log_solution(self) -> str:
        """
        Logs the solution.

        If a solution isn't available a proper message is displayed.
        """
        if not getattr(self, "solution", False):
            hyperLogger.warning("No solving operation has been concluded.")
            return

        log = ["\nSolution Log:"]
        percent_items_stored = sum([len(i) for cont_id, i in self.solution.items()]) / len(
            self._items
        )
        log.append(f"Percent total items stored : {percent_items_stored*100:.4f}%")

        for cont_id in self._containers:
            L = self._get_container_height(cont_id)
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

    def reset_container_height(self):
        """
        Resets the imaginary (strip packing) container's height.
        If called form bin packing instace, nothing happens.
        """
        if self._strip_pack:
            self._container_height = (
                self.containers[self.STRIP_PACK_CONT_ID]["W"] * self.MAX_W_L_RATIO
            )
            self._container_min_height = None
        else:
            return

    # % ----------- PROPERTIES -----------

    @property
    def items(self):
        return self._items

    @items.setter
    def items(self, value):
        self._items = Items(value, self)

    @items.deleter
    def items(self):
        raise ItemsError("CANT_DELETE")

    # % -----------------------------

    @property
    def containers(self):
        return self._containers

    @containers.setter
    def containers(self, value):
        if self._strip_pack:
            raise ContainersError("STRIP_PACK_ONLY")
        self._containers = Containers(value, self)
        self._containers_num = len(value)

    @containers.deleter
    def containers(self):
        raise ContainersError("CANT_DELETE")

    # % -----------------------------

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

    # % -----------------------------

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

    # % -----------------------------

    @property
    def container_height(self):
        return self._container_height

    @container_height.setter
    def container_height(self, value):
        if not isinstance(value, int) or value < 1:
            raise DimensionsError("DIMENSION_VALUE")

        if self._container_min_height is not None:
            if value < self._container_min_height:
                raise ContainersError("STRIP_PACK_MIN_HEIGHT")

        self._container_height = value

    @container_height.deleter
    def container_height(self):
        raise DimensionsError("CANT_DELETE")

    # % -----------------------------

    @property
    def container_min_height(self):
        return self._container_min_height

    @container_min_height.setter
    def container_min_height(self, value):
        if not isinstance(value, int) or value < 1:
            raise DimensionsError("DIMENSION_VALUE")

        if value > self._container_height:
            raise ContainersError("STRIP_PACK_MIN_HEIGHT")

        self._container_min_height = value

    @container_min_height.deleter
    def container_min_height(self):
        raise DimensionsError("CANT_DELETE")


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
            return sum([u for u in containers_obj_vals[:-1]]) + 0.7 * containers_obj_vals[-1]

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
            self._set_container_height()
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
                f"\t\tCURRENT POTENTIAL POINTS STRATEGY: {self._potential_points_strategy}"
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
    This class extends ``PointGenPack``, utilizing it's solving functionalities
    by implementing:

        **A.** a hill-climbing, 2-opt exchange local search

        **B.** a hypersearch hyper-heuristic.
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
            self.STRATEGIES_SUFFIX_STRIPACK if self._strip_pack else self.STRATEGIES_SUFFIX
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
                    items=self.items.deepcopy(),
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
            raise MultiProcessError("ALL_PROCESSES_FAILED")
        elif -1 in shared_list:
            hyperLogger.error("Some of the processes raised an exception. Please check logs.")

        # get winning process and update instance data
        shared_list_optimum = self._get_array_optimum(shared_list)
        win_process_index = shared_list.index(shared_list_optimum)
        win_process = processes[win_process_index]
        win_metrics = win_process.queue.get()

        best_solution = self._deepcopy_solution(win_metrics[1])
        best_obj_val_per_container = self._copy_objective_val_per_container(win_metrics[2])
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

        hyperLogger.info("Initiating Hypersearch.")

        strategies = self.get_strategies(_exhaustive=_exhaustive)

        self.solution, self.obj_val_per_container, self.best_strategy = (
            self._single_process_hypersearch(strategies, throttle)
            if self._workers_num == 1
            else self._multi_process_hypersearch(
                strategies, throttle, _force_raise_error_index
            )
        )

        hyperLogger.info("Hypersearch terminated")

        total_time = time.time() - self.start_time
        hyperLogger.debug(f"Execution time : {total_time} [sec]")
