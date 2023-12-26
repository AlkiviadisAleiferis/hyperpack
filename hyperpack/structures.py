"""
This module contains the COntainers, Items structures
used by PointGenPack and HyperPack
to solve the corresponding problems.

Each Containers, Items instance is a dictionary.

Each Containers key is a container, and it's value is a Dimensions
dictionary. Same stands for Items structure set.

Each Dimensions instance is a dictionary with two keys only.

e.g.
containers = {
    "container-id-0": Dimensions,
    "container-id-1": Dimensions,
    "container-id-2": Dimensions,
}
items = {
    "item-id-0": Dimensions,
    "item-id-1": Dimensions,
    "item-id-2": Dimensions,
}

The above structure is inavoidable.
"""

from collections import UserDict

from .exceptions import ContainersError, DimensionsError, ItemsError
from .loggers import hyperLogger


class Dimensions(UserDict):
    """
    Dictionary representing structure's dimensions (Width, Length).

    Stores ``HyperPack``'s instance in ``self.instace`` for ``solution`` resetting
    upon changes.
    """

    def __init__(self, dimensions=None, reference_structure=None, instance=None):
        # dimensions = {
        #   "w or W": int,
        #   "l or W": int
        # }

        # it is propagated from Structure. Problem instance
        self.instance = instance

        if reference_structure.__class__ not in (Containers, Items):
            raise DimensionsError(DimensionsError.DIMENSIONS_REFERENCE_OBJECT)

        self.proper_keys = set(reference_structure.PROPER_DIMENSIONS_KEYS)

        if dimensions is None or dimensions == {}:
            raise DimensionsError(DimensionsError.DIMENSIONS_MISSING)

        if not isinstance(dimensions, dict):
            raise DimensionsError(DimensionsError.DIMENSIONS_TYPE)

        if set(dimensions) != self.proper_keys:
            raise DimensionsError(DimensionsError.DIMENSIONS_KEYS)

        self.data = {}
        for key in dimensions:
            self.validate_data(key, dimensions[key])
            self.data[key] = dimensions[key]

        if self.instance is not None:
            self.reset_instance_attrs()

    def reset_instance_attrs(self):
        self.instance.obj_val_per_container = {}
        self.instance.solution = {}

    def validate_data(self, key, item):
        """
        key must be "W" or "L" / "w" or "l".
        value must be positive number.
        """
        if key not in self.proper_keys:
            raise DimensionsError(DimensionsError.DIMENSIONS_KEYS)

        try:
            if not isinstance(item, int) or item <= 0:
                raise DimensionsError
        except Exception:
            raise DimensionsError(DimensionsError.DIMENSION_VALUE)

    def __setitem__(self, key, item):
        """
        This method takes place on operations as this:
        Structures["structure_id"]["dimension"] = value.

        Resetting of attributes is enforced through stored instance.

        Proper dimensions format enforced.
        """
        if (
            self.instance._strip_pack
            and self.proper_keys == {"W", "L"}
            and self.data != {}
        ):
            raise ContainersError(ContainersError.STRIP_PACK_ONLY)

        self.validate_data(key, item)

        self.data[key] = item

        if self.instance is not None:
            self.reset_instance_attrs()

    def __delitem__(self, key):
        raise DimensionsError(DimensionsError.CANT_DELETE)


class AbstractStructureSet(UserDict):
    """
    Abstract class encapsulating the structure attribute (nested dicitonary)
    of the HyperPack class.

    Every key (structure id) has a Dimensions dictionary object as value.

    Makes sure that assignment and value changes in the objects of this class
        1. are validated on run
        2. hyperpack 's instances solution attribute reset's
    """

    PROPER_DIMENSIONS_KEYS = None

    def __init__(self, structure=None, instance=None):
        self.instance = instance

        if structure is None or structure == {}:
            raise self.ERROR_CLASS(self.ERROR_CLASS.MISSING)

        if not isinstance(structure, dict):
            raise self.ERROR_CLASS(self.ERROR_CLASS.TYPE)

        self.data = {}

        for structure_id in structure:
            self.data[structure_id] = self.get_structure_dimensions(
                structure_id, structure[structure_id]
            )

    def __setitem__(self, structure_id, new_dims):
        """
        This method takes place on operations as this:
        Structures["structure_id"] = dimensions value (dict).

        Resetting of attributes is enforced through stored instance.

        Proper structure_id format enforced.
        """
        if self.instance._strip_pack and self.__class__.__name__ == "Containers":
            raise ContainersError(ContainersError.STRIP_PACK_ONLY)

        self.data[structure_id] = self.get_structure_dimensions(structure_id, new_dims)

        if self.instance is not None:
            self.reset_instance_attrs()

    def __delitem__(self, key):
        if len(self.data) == 1:
            raise self.ERROR_CLASS(self.ERROR_CLASS.CANT_DELETE_STRUCTURE)
        del self.data[key]
        self.reset_instance_attrs()

    def get_structure_dimensions(self, structure_id, dims):
        # The structure's dimension is an instance
        # of the Dimensions class
        if not isinstance(structure_id, str):
            raise self.ERROR_CLASS(self.ERROR_CLASS.ID_TYPE)

        return Dimensions(dims, self, self.instance)

    def reset_instance_attrs(self):
        self.instance.obj_val_per_container = {}
        self.instance.solution = {}

    def deepcopy(self, ids_sequence=None):
        if ids_sequence is None:
            return {
                structure_id: {
                    dimension: self.data[structure_id][dimension]
                    for dimension in self.data[structure_id]
                }
                for structure_id in self.data
            }
        else:
            return {
                structure_id: {
                    dimension: self.data[structure_id][dimension]
                    for dimension in self.data[structure_id]
                }
                for structure_id in ids_sequence
            }


class Containers(AbstractStructureSet):
    """
    Class encapsulating the containers attribute (nested dicitonary)
    of the HyperPack class, by proper subclassing of AbstractStructureSet.
    """

    PROPER_DIMENSIONS_KEYS = ("W", "L")
    ERROR_CLASS = ContainersError

    def __init__(self, containers=None, instance=None):
        super().__init__(structure=containers, instance=instance)

    def reset_instance_attrs(self):
        super().reset_instance_attrs()
        self.instance._containers_num = len(self.data)

    def _get_height(self, cont_id="strip-pack-container"):
        """
        **Calculates and returns the container's height.**

        In case of bin-packing:
            it returns the containers height.

        In case of strip packing:
            if a solution has been found return
            ``instance._container_min_height`` OR
            height of items stack in solution

            if a solution has not been found, return
            (container Width)* ``instance.MAX_W_L_RATIO``

        Used in:
            ``instance.create_figure``

            ``instance.log_solution``
        """
        if getattr(self.instance, "_strip_pack", False):
            if not getattr(self.instance, "solution", {}):
                return self.data[cont_id]["W"] * self.instance.MAX_W_L_RATIO

            else:
                solution = self.instance.solution[cont_id]
                # height of items stack in solution
                solution_height = max(
                    [solution[item_id][1] + solution[item_id][3] for item_id in solution]
                    or [0]
                )

                # preventing container height to drop below point
                if self.instance._container_min_height is not None:
                    return max(solution_height, self.instance._container_min_height)

                return solution_height
        else:
            return self.data[cont_id]["L"]

    def _set_height(self):
        cont_id = self.instance.STRIP_PACK_CONT_ID

        if not getattr(self.instance, "solution", {}):
            height = self.data[cont_id]["W"] * self.MAX_W_L_RATIO

        else:
            solution = self.instance.solution[cont_id]
            # height of items stack in solution
            solution_height = max(
                [solution[item_id][1] + solution[item_id][3] for item_id in solution]
                or [0]
            )

            # preventing container height to drop below point
            if self.instance._container_min_height is not None:
                height = max(solution_height, self.instance._container_min_height)
            else:
                height = solution_height

        self.instance._container_height = height

    def __str__(self):
        strings_list = []
        class_name = "Containers"
        width_key = self.PROPER_DIMENSIONS_KEYS[0]
        length_key = self.PROPER_DIMENSIONS_KEYS[1]

        strings_list.append(class_name)
        for structure_id in self.data:
            width = self.data[structure_id][width_key]
            length = self.data[structure_id][length_key]

            if self.instance._strip_pack:
                strings_list.append(f"  - id: {structure_id}\n    width: {width}\n")
            else:
                strings_list.append(
                    f"  - id: {structure_id}\n    width: {width}\n    length: {length}\n"
                )

        return "\n".join(strings_list)


class Items(AbstractStructureSet):
    """
    Class encapsulating the items attribute (nested dicitonary)
    of the HyperPack class, by proper subclassing of AbstractStructureSet.
    """

    PROPER_DIMENSIONS_KEYS = ("w", "l")
    ERROR_CLASS = ItemsError

    def __init__(self, items=None, instance=None):
        super().__init__(structure=items, instance=instance)

    def __str__(self):
        strings_list = []
        class_name = "Items"
        width_key = self.PROPER_DIMENSIONS_KEYS[0]
        length_key = self.PROPER_DIMENSIONS_KEYS[1]

        strings_list.append(class_name)
        for structure_id in self.data:
            width = self.data[structure_id][width_key]
            length = self.data[structure_id][length_key]
            strings_list.append(
                f"  - id: {structure_id}\n    width: {width}\n    length: {length}\n"
            )

        return "\n".join(strings_list)
