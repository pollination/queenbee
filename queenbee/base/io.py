"""Input and Output (IO) objects."""
import collections
from typing import List
from pydantic import validator

from .basemodel import BaseModel


def find_dup_items(values: List) -> List:
    """Find duplicate items in a list

    Arguments:
        values {List} -- A list of items

    Returns:
        List -- A list of duplicated items
    """
    dup = [t for t, c in collections.Counter(values).items() if c > 1]
    return dup


class IOItem(BaseModel):

    name: str


class IOBase(BaseModel):
    """A reusable model for Input and Output (IO) objects.

    IOBase is used within Operators, Recipes and Workflows.
    """

    parameters: List[IOItem]

    artifacts: List[IOItem]

    @validator('parameters', 'artifacts')
    def parameter_unique_names(cls, v):
        """Pydantic validator to check that IO item names are unique within their list

        Arguments:
            v {list} -- A list of items

        Raises:
            ValueError: Duplicate names have been found

        Returns:
            list -- The accepted list of items
        """
        names = [value.name for value in v]
        duplicates = find_dup_items(names)
        if len(duplicates) != 0:
            raise ValueError(f'Duplicate names: {duplicates}')
        return v

    @validator('parameters', 'artifacts', always=True)
    def empty_list(cls, v):
         return [] if v is None else v

    @validator('parameters', 'artifacts')
    def sort_list(cls, v):
        """Pydantic validator to sort IO items by name

        Arguments:
            v {list} -- A list of items

        Returns:
            list -- The accepted list of items
        """
        v.sort(key=lambda x: x.name)
        return v

    @staticmethod
    def _by_name(
        input_list: list,
        name: str,
    ):
        """Retrieve an item from a list by its name attribute

        Arguments:
            input_list {list} -- A list of IO Items
            name {str} -- The name to filter for

        Raises:
            ValueError: No item with this name was found

        Returns:
            IOItem -- An IO Item with the input name
        """
        if input_list is None:
            raise ValueError(f'no value with name {name} exists in: \n{input_list}')
        res = [x for x in input_list if x.name == name]
        if res == []:
            raise ValueError(f'no value with name {name} exists in: \n{input_list}')

        return res[0]

    def artifact_by_name(self, name: str):
        """Retrieve an artifact from the IOBase model by name

        Arguments:
            name {str} -- The name to search for

        Returns:
            IOItem -- An IO Item with the input name
        """
        return self._by_name(self.artifacts, name)

    def parameter_by_name(self, name: str):
        """Retrieve an parameter from the IOBase model by name

        Arguments:
            name {str} -- The name to search for

        Returns:
            IOItem -- An IO Item with the input name
        """
        return self._by_name(self.parameters, name)
