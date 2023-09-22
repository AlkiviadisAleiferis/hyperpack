from .loggers import hyperLogger


class ErrorLoggingException(Exception):
    """
    Exception Class that manages error logging.
    """

    logger = hyperLogger

    def __init__(self, message=None, **kwargs):
        if message is not None:
            if message.isupper():
                message = getattr(self, message, None)
            self.log_error(message)
        super().__init__(message)

    def log_error(self, message=None, **kwargs):
        self.logger.error(message)


class ContainersError(ErrorLoggingException):
    MISSING = "containers missing."
    TYPE = "containers must be of type dict."
    ID_TYPE = "container id must be of type str."
    CANT_DELETE_STRUCTURE = "Can't remove any more containers."
    CANT_DELETE = "Can't delete containers structure."
    STRIP_PACK_ONLY = "Can't assign or change containers when solving strip-packing."
    STRIP_PACK_MIN_HEIGHT = "Min container height must be less or equal to actual height."


class ItemsError(ErrorLoggingException):
    MISSING = "items missing."
    TYPE = "items must be of type dict."
    ID_TYPE = "item id must be of type str."
    CANT_DELETE_STRUCTURE = "Can't remove any more items."
    CANT_DELETE = "Can't delete items structure."


class SettingsError(ErrorLoggingException):
    CANT_DELETE_SETTINGS = "Cant delete settings attribute"
    TYPE = "settings must be of type dict."
    MAX_TIME_IN_SECONDS_TYPE = "settings-->'max_time_in_seconds': value must be of type int."
    MAX_TIME_IN_SECONDS_VALUE = (
        "settings-->'max_time_in_seconds': value must be positive integer."
    )
    WORKERS_NUM_VALUE = "settings-->'workers_num': value must be positive integer."
    WORKERS_NUM_CPU_COUNT_WARNING = "you are trying to set more workers than your cpu threads."
    ROTATION_TYPE = "settings-->'rotation': value must be of type boolean."
    FIGURE_KEY_TYPE = "settings-->'figure': value must be of type dict."
    PLOTLY_NOT_INSTALLED = "plotly library is not installed."
    PLOTLY_VERSION = "plotly library must be at least 5.14.0 version."
    FIGURE_EXPORT_VALUE_TYPE = "settings-->figure-->'export': key value must be of type dict."
    FIGURE_EXPORT_TYPE_MISSING = "settings-->figure-->export-->'type': key wasn't provided."
    FIGURE_EXPORT_TYPE_VALUE = (
        "settings-->figure-->export-->'type': has "
        "wrong value. Choices are ('html', 'image')."
    )
    FIGURE_EXPORT_PATH_MISSING = "settings-->figure-->export-->'path': key wasn't provided."
    FIGURE_EXPORT_PATH_VALUE = (
        "settings-->figure-->export-->'path': value must be of type string."
    )
    FIGURE_EXPORT_PATH_NOT_EXISTS = "figure export path doesn't exist."
    FIGURE_EXPORT_PATH_NOT_DIRECTORY = "figure export path must be a directory."
    FIGURE_EXPORT_FORMAT_MISSING = (
        "settings-->figure-->export-->'format': key wasn't provided."
    )
    FIGURE_EXPORT_FORMAT_TYPE = (
        "settings-->figure-->export-->'format': value must be of type string."
    )
    FIGURE_EXPORT_FORMAT_VALUE = (
        "settings-->figure-->export-->'format': value must be in"
        " (pdf, png, jpeg, webp, svg) for image exportation."
    )
    FIGURE_EXPORT_FILE_NAME_TYPE = (
        "settings-->figure-->export-->'file_name': value must be of type string."
    )
    FIGURE_EXPORT_FILE_NAME_VALUE = (
        "settings-->figure-->export-->'file_name': value has improper string characters."
    )
    FIGURE_EXPORT_KALEIDO_MISSING = "Cant export figure to image, kaleido library missing."
    FIGURE_EXPORT_KALEIDO_VERSION = (
        "kaleido library version must be at least 0.2.1. Cant export to image."
    )
    FIGURE_EXPORT_WIDTH_VALUE = (
        "settings-->figure-->export-->'width': value must be positive integer"
    )
    FIGURE_EXPORT_HEIGHT_VALUE = (
        "settings-->figure-->export-->'height': value must be positive integer"
    )
    FIGURE_SHOW_VALUE = "settings-->figure-->'show': value must be of type boolean."


class DimensionsError(ErrorLoggingException):
    DIMENSIONS_MISSING = "dimensions are missing."
    DIMENSIONS_TYPE = "dimensions must be of type dict."
    DIMENSIONS_KEYS = "dimensions must (only) contain Width and Length keys."
    DIMENSION_VALUE = "Width and Length must be positive integers."
    # mostly inner workings exception
    DIMENSIONS_REFERENCE_OBJECT = "Neither container or item reference structure provided."
    CANT_DELETE = "Can't delete a dimension."


class FigureExportError(ErrorLoggingException):
    FIGURE_EXPORT = "ERROR at figure exportation:\n\t {}."
    NO_SOLUTION_WARNING = "Can't create figure if a solution hasn't been found."
    NO_FIGURE_OPERATION = (
        "If not showing or exporting the figure makes the operation obsolete."
    )


class MultiProcessError(ErrorLoggingException):
    ALL_PROCESSES_FAILED = "All hypersearch processes failed."


class PotentialPointsError(ErrorLoggingException):
    TYPE = "Wrong potential points strategy type." "Must be of type tuple."
    ELEMENT_TYPE = "Wrong potential points strategy format." "Elements must be of type str."
    ELEMENT_NOT_POINT = (
        "Wrong potential points strategy format." "Elements must be potential points."
    )
    DELETE = "Cannot delete potential_points_strategy attribute."
    DUPLICATE_POINTS = "No duplicate potential points allowed."
