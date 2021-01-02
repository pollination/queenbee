"""common objects between different IO files."""
import collections

from enum import Enum
from typing import Dict, List, Any

from pydantic import constr, Field, validator

from .reference import FolderReference, FileReference, references_from_string
from ..base.basemodel import BaseModel


class ItemType(str, Enum):
    """Type enum for items in a list.

    Items can not be files or folder. For a list of files you should copy them to a
    folder and use FolderInput input instead of using ArrayInput.
    """
    Generic = 'Generic'  # generic type for inputs with no type hint.
    String = 'String'
    Integer = 'Integer'
    Number = 'Number'
    Boolean = 'Boolean'
    Array = 'Array'  # set item type to a generic type
    JSONObject = 'JSONObject'


class GenericInput(BaseModel):
    """Base class for all input types."""

    type: constr(regex='^GenericInput$') = 'GenericInput'

    name: str = Field(
        ...,
        description='Input name.'
    )

    description: str = Field(
        None,
        description='Optional description for input.'
    )

    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        """Get all referenced values specified by var name.

        Returns:
            Dict[str, List[str]] -- A dictionary where each key corresponds to a class
                attribute indexing a list of referenced values.
        """
        return self._referenced_values(['default'])

    @property
    def is_artifact(self):
        return False

    @property
    def is_parameter(self):
        return not self.is_artifact


class GenericOutput(BaseModel):
    """Base class for all output types.

    The baseclass uses a name to source the output.
    """

    type: constr(regex='^GenericOutput$') = 'GenericOutput'

    name: str = Field(
        ...,
        description='Output name.'
    )

    description: str = Field(
        None,
        description='Optional description for output.'
    )

    @property
    def is_artifact(self):
        return False

    @property
    def is_parameter(self):
        return not self.is_artifact


class PathOutput(GenericOutput):
    """Base class for output classes that source tha output from a path.

    An example of using PathOutput is TaskFile and TaskFolder outputs.
    """

    type: constr(regex='^PathOutput$') = 'PathOutput'

    path: str = Field(
        ...,
        description='Path to the output artifact relative to where the function command '
        'is executed.'
        )

    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        """Get referenced variables if any.

        Returns:
            Dict[str, List[str]] -- A dictionary where keys are attributes and values
                are lists contain referenced value string.
        """
        return self._referenced_values(['path'])


class FromOutput(GenericOutput):
    """Base class for output classes that source ``from`` an object.

    See DAG output classes for more examples.
    """
    type: constr(regex='^FromOutput$') = 'FromOutput'

    # This will be overwritten in all the subclasses.
    # We need this here to make sure the validator doesn't fail.
    from_: Any = Field(
        ...,
        description='Reference to a file or a task output. Task output must be file.',
        alias='from'
    )

    @validator('from_')
    def check_folder_artifact_has_no_refs(cls, v):
        if isinstance(v, (FolderReference, FileReference)):
            refs = references_from_string(v.path)
            if refs != []:
                raise ValueError(
                    'DAG Output `from` of type '
                    '`folder` cannot use templated values in its '
                    f'path: {v.path}'
                )

        return v


def find_dup_items(values: List) -> List:
    """Find duplicate items in a list

    Arguments:
        values {List} -- A list of items

    Returns:
        List -- A list of duplicated items
    """
    dup = [t for t, c in collections.Counter(values).items() if c > 1]
    return dup


def find_io_by_name(input_list: list, name: str):
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
        raise ValueError(
            f'no value with name {name} exists in: \n{input_list}')
    res = [x for x in input_list if x.name == name]
    if res == []:
        raise ValueError(
            f'no value with name {name} exists in: \n{input_list}')

    return res[0]


class IOBase(BaseModel):
    """A reusable model for classes with Input and Output (IO) objects.

    IOBase is the baseclass for Function, DAG and Workflow.
    """

    type: constr(regex='^IOBase$') = 'IOBase'

    inputs: List[Any] = Field(
        None,
        description='Place-holder. Overwrite this!'
    )

    outputs: List[Any] = Field(
        None,
        description='Place-holder. Overwrite this!'
    )

    @validator('inputs', 'outputs', always=True)
    def parameter_unique_names(cls, v):
        """Pydantic validator to check that IO item names are unique within their list

        Arguments:
            v {list} -- A list of items

        Raises:
            ValueError: Duplicate names have been found

        Returns:
            list -- The accepted list of items
        """
        if v is None:
            return []
        names = [value.name for value in v]
        duplicates = find_dup_items(names)
        if len(duplicates) != 0:
            raise ValueError(f'Duplicate names: {duplicates}')
        return v

    @validator('inputs', 'outputs')
    def sort_list(cls, v):
        """Pydantic validator to sort IO items by name

        Arguments:
            v {list} -- A list of items

        Returns:
            list -- The accepted list of items
        """
        v.sort(key=lambda x: x.name)
        return v

    @property
    def artifacts(self) -> Dict:
        """Get input and output artifacts. Artifacts are file, folder and path inputs.

        Returns:
            Dict -- A dictionary with two keys for inputs and outputs. Each key includes
                a list of artifacts.
        """
        artifact_inputs = [inp for inp in self.inputs if inp.is_artifact]
        artifact_outputs = [inp for inp in self.outputs if inp.is_artifact]

        return {'inputs': artifact_inputs, 'outputs': artifact_outputs}

    @property
    def artifact_inputs(self) -> List:
        """Get input artifacts. Artifacts are file, folder and path inputs.

        Returns:
            A list -- A list of input artifacts.
        """
        artifact_inputs = [inp for inp in self.inputs if inp.is_artifact]

        return artifact_inputs

    @property
    def artifact_outputs(self) -> List:
        """Get output artifacts. Artifacts are file, folder and path inputs.

        Returns:
            A list -- A list of output artifacts.
        """
        artifact_outputs = [inp for inp in self.outputs if inp.is_artifact]

        return artifact_outputs

    def artifact_input_by_name(self, name: str):
        """Retrieve an artifact from the inputs by name

        Arguments:
            name {str} -- The name to search for

        Returns:
            IOItem -- An IO Item with the input name
        """
        return find_io_by_name(self.artifact_inputs, name)

    def artifact_output_by_name(self, name: str):
        """Retrieve an artifact from the outputs by name

        Arguments:
            name {str} -- The name to search for

        Returns:
            IOItem -- An IO Item with the input name
        """
        return find_io_by_name(self.artifact_outputs, name)

    @property
    def parameters(self) -> Dict:
        """Get input and output parameters.

        Returns:
            Dict -- A dictionary with two keys for inputs and outputs. Each key includes
                a list of parameters.
        """
        parameter_inputs = [inp for inp in self.inputs if not inp.is_artifact]
        parameter_outputs = [inp for inp in self.outputs if not inp.is_artifact]

        return {'inputs': parameter_inputs, 'outputs': parameter_outputs}

    @property
    def parameter_inputs(self) -> List:
        """Get input parameters. Parameters are non file, folder and path inputs.

        Returns:
            A list -- A list of input parameters.
        """
        parameter_inputs = [inp for inp in self.inputs if inp.is_parameter]

        return parameter_inputs

    @property
    def parameter_outputs(self) -> List:
        """Get output parameters. Parameters are non file, folder and path inputs.

        Returns:
            A list -- A list of output parameters.
        """
        parameter_outputs = [inp for inp in self.outputs if inp.is_parameter]

        return parameter_outputs

    def parameter_input_by_name(self, name: str):
        """Retrieve an parameter from the inputs by name

        Arguments:
            name {str} -- The name to search for

        Returns:
            IOItem -- An IO Item with the input name
        """
        return find_io_by_name(self.parameter_inputs, name)

    def parameter_output_by_name(self, name: str):
        """Retrieve an parameter from the outputs by name

        Arguments:
            name {str} -- The name to search for

        Returns:
            IOItem -- An IO Item with the input name
        """
        return find_io_by_name(self.parameter_outputs, name)


class IOAliasHandler(BaseModel):
    """Input and output alias handler object."""

    type: constr(regex='^IOAliasHandler$') = 'IOAliasHandler'

    language: str = Field(
        ...,
        description='Declare the language (e.g. python, csharp, etc.). This '
        'option allows the recipe to be flexible on handling different programming '
        'languages.'
    )

    module: str = Field(
        ...,
        description='Target module or namespace to load the alias function.',
        example='honeybee_rhino.handlers'
    )

    function: str = Field(
        ...,
        description='Name of the function. The input value will be passed to this '
        'function as the first argument.'
    )
