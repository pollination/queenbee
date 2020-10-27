"""common objects between different IO files."""
import collections

from enum import Enum
from typing import Dict, List, Any

from pydantic import constr, Field, validator
from jsonschema import validate as json_schema_validator

from .reference import FolderReference, FileReference, references_from_string
from ..base.basemodel import BaseModel
from ..base.variable import validate_inputs_outputs_var_format, get_ref_variable


class ItemType(str, Enum):
    """Type enum for items in a list."""
    String = 'String'
    Integer = 'Integer'
    Number = 'Number'
    Boolean = 'Boolean'
    Folder = 'Folder'
    Array = 'Array'
    Object = 'Object'


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

    default: str = Field(
        None,
        description='Place-holder. Overwrite this!'
    )

    spec: Dict = Field(
        None,
        description='An optional JSON Schema specification to validate the input value. '
        'You can use validate_spec method to validate a value against the spec.'
    )

    @validator('default')
    def validate_default_refs(cls, v, values):
        """Validate referenced variables in the command"""
        try:
            type_ = values['type']
        except KeyError:
            raise ValueError(f'Input with missing type: {cls.__name__}')

        if type_ != cls.__name__ or not isinstance(v, (str, bytes)):
            # this is a check to ensure the default value only gets validated againt the
            # correct class type. See spec validation for more information
            return v

        ref_var = get_ref_variable(v)
        add_info = []
        for ref in ref_var:
            add_info.append(validate_inputs_outputs_var_format(ref))

        if add_info:
            raise ValueError('\n'.join(add_info))

        return v

    @validator('spec')
    def validate_default_value(cls, v, values):
        """Validate default value against spec if provided."""
        try:
            type_ = values['type']
        except KeyError:
            raise ValueError(f'Input with missing type: {cls.__name__}')

        if type_ != cls.__name__:
            # this is a check to ensure the default value only gets validated againt the
            # correct class type. The reason we need to do this is that Pydantic doesn't
            # support discriminators (https://github.com/samuelcolvin/pydantic/issues/619).
            # As a result in case of checking for Union it checks every possible item
            # from the start until it finds one. For inputs it causes this check to fail
            # on a string before it gets to the integer class for an integer input.
            return v

        try:
            default = values['default']
        except KeyError:
            # spec is not set
            return v

        if v is not None and default is not None:
            json_schema_validator(default, v)
        return v

    def validate_spec(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        if self.spec:
            spec = dict(self.spec)
            json_schema_validator(value, spec)
        return value

    @property
    def required(self):
        """Check if input is required."""
        return True if not self.default else False

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
        input_artifacts = [inp for inp in self.inputs if inp.is_artifact]
        output_artifacts = [inp for inp in self.outputs if inp.is_artifact]

        return {'inputs': input_artifacts, 'outputs': output_artifacts}

    @property
    def input_artifacts(self) -> List:
        """Get input artifacts. Artifacts are file, folder and path inputs.

        Returns:
            A list -- A list of input artifacts.
        """
        input_artifacts = [inp for inp in self.inputs if inp.is_artifact]

        return input_artifacts

    @property
    def output_artifacts(self) -> List:
        """Get output artifacts. Artifacts are file, folder and path inputs.

        Returns:
            A list -- A list of output artifacts.
        """
        output_artifacts = [inp for inp in self.outputs if inp.is_artifact]

        return output_artifacts

    def input_artifact_by_name(self, name: str):
        """Retrieve an artifact from the inputs by name

        Arguments:
            name {str} -- The name to search for

        Returns:
            IOItem -- An IO Item with the input name
        """
        return find_io_by_name(self.input_artifacts, name)

    def output_artifact_by_name(self, name: str):
        """Retrieve an artifact from the outputs by name

        Arguments:
            name {str} -- The name to search for

        Returns:
            IOItem -- An IO Item with the input name
        """
        return find_io_by_name(self.output_artifacts, name)

    @property
    def parameters(self) -> Dict:
        """Get input and output parameters.

        Returns:
            Dict -- A dictionary with two keys for inputs and outputs. Each key includes
                a list of parameters.
        """
        input_parameters = [inp for inp in self.inputs if not inp.is_artifact]
        output_parameters = [inp for inp in self.outputs if not inp.is_artifact]

        return {'inputs': input_parameters, 'outputs': output_parameters}

    @property
    def input_parameters(self) -> List:
        """Get input parameters. Parameters are file, folder and path inputs.

        Returns:
            A list -- A list of input parameters.
        """
        input_parameters = [inp for inp in self.inputs if inp.is_parameter]

        return input_parameters

    @property
    def output_parameters(self) -> List:
        """Get output parameters. Parameters are file, folder and path inputs.

        Returns:
            A list -- A list of output parameters.
        """
        output_parameters = [inp for inp in self.outputs if inp.is_parameter]

        return output_parameters

    def input_parameter_by_name(self, name: str):
        """Retrieve an parameter from the inputs by name

        Arguments:
            name {str} -- The name to search for

        Returns:
            IOItem -- An IO Item with the input name
        """
        return find_io_by_name(self.input_parameters, name)

    def output_parameter_by_name(self, name: str):
        """Retrieve an parameter from the outputs by name

        Arguments:
            name {str} -- The name to search for

        Returns:
            IOItem -- An IO Item with the input name
        """
        return find_io_by_name(self.output_parameters, name)
