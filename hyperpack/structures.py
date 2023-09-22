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

        # it is propagated from Structure
        self.instance = instance
        if reference_structure not in {"item", "container"}:
            raise DimensionsError("DIMENSIONS_REFERENCE_OBJECT")

        if reference_structure == "item":
            self.proper_keys = {"w", "l"}
        else:
            self.proper_keys = {"W", "L"}

        if dimensions is None or dimensions == {}:
            raise DimensionsError("DIMENSIONS_MISSING")

        if not isinstance(dimensions, dict):
            raise DimensionsError("DIMENSIONS_TYPE")

        if not set(dimensions) == self.proper_keys:
            raise DimensionsError("DIMENSIONS_KEYS")

        self.data = {}
        for key in dimensions:
            self.check_data(key, dimensions[key])
            self.data[key] = dimensions[key]

        if self.instance is not None:
            self.reset_instance_attrs()

    def reset_instance_attrs(self):
        self.instance.obj_val_per_container = {}
        self.instance.solution = {}

    def check_data(self, key, item):
        """
        key must be "W" or "L" / "w" or "l".
        value must be positive number.
        """
        if key not in self.proper_keys:
            raise DimensionsError("DIMENSIONS_KEYS")

        try:
            if not isinstance(item, int) or item <= 0:
                raise DimensionsError
        except Exception:
            raise DimensionsError("DIMENSION_VALUE")

    def __setitem__(self, key, item):
        """
        This method takes place on operations as this:
        Structures["structure_id"]["dimension"] = value.

        Resetting of attributes is enforced through stored instance.

        Proper dimensions format enforced.
        """
        if self.instance._strip_pack and self.proper_keys == {"W", "L"} and self.data != {}:
            raise ContainersError("STRIP_PACK_ONLY")

        self.check_data(key, item)
        self.data[key] = item
        if self.instance is not None:
            self.reset_instance_attrs()

    def __delitem__(self, key):
        raise DimensionsError("CANT_DELETE")


class AbstractStructure(UserDict):
    """
    Abstract class encapsulating the structure attribute (nested dicitonary)
    of the HyperPack class.

    Every key (structure id) has a Dimensions dictionary object as value.

    Makes sure that assignment and value changes in the objects of this class
        1. are validated on run
        2. hyperpack 's instances solution attribute reset's
    """

    def __init__(self, structure=None, instance=None):
        self.instance = instance
        if structure is None or structure == {}:
            raise self.ERROR_CLASS("MISSING")

        if not isinstance(structure, dict):
            raise self.ERROR_CLASS("TYPE")

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
            raise ContainersError("STRIP_PACK_ONLY")

        self.data[structure_id] = self.get_structure_dimensions(structure_id, new_dims)
        if self.instance is not None:
            self.reset_instance_attrs()

    def __delitem__(self, key):
        if len(self.data) == 1:
            raise self.ERROR_CLASS("CANT_DELETE_STRUCTURE")
        del self.data[key]
        self.reset_instance_attrs()

    def get_structure_dimensions(self, structure_id, dims):
        # The structure's dimension is an instance
        # of the Dimensions class
        class_name = self.__class__.__name__
        reference_structure = "container" if class_name == "Containers" else "item"

        if not isinstance(structure_id, str):
            raise self.ERROR_CLASS("ID_TYPE")

        return Dimensions(dims, reference_structure, self.instance)

    def reset_instance_attrs(self):
        self.instance.obj_val_per_container = {}
        self.instance.solution = {}

    def __str__(self):
        strings_list = []
        class_name = self.__class__.__name__
        width_key = "W" if class_name == "Containers" else "w"
        length_key = "L" if class_name == "Containers" else "l"

        strings_list.append(class_name)
        for structure_id in self.data:
            width = self.data[structure_id][width_key]
            length = self.data[structure_id][length_key]

            if self.instance._strip_pack and class_name == "Containers":
                strings_list.append(f"  - id: {structure_id}\n    width: {width}\n")
            else:
                strings_list.append(
                    f"  - id: {structure_id}\n    width: {width}\n    length: {length}\n"
                )
        return "\n".join(strings_list)

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


class Containers(AbstractStructure):
    """
    Class encapsulating the containers attribute (nested dicitonary)
    of the HyperPack class, by proper subclassing of AbstractStructure.
    """

    ERROR_CLASS = ContainersError

    def __init__(self, containers=None, instance=None):
        super().__init__(structure=containers, instance=instance)

    def reset_instance_attrs(self):
        super().reset_instance_attrs()
        self.instance._containers_num = len(self.data)


class Items(AbstractStructure):
    """
    Class encapsulating the items attribute (nested dicitonary)
    of the HyperPack class, by proper subclassing of AbstractStructure.
    """

    ERROR_CLASS = ItemsError

    def __init__(self, items=None, instance=None):
        super().__init__(structure=items, instance=instance)
