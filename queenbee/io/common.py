"""common objects between different IO files."""
from enum import Enum
from typing import Dict, List, Any

from pydantic import constr, Field, validator
from jsonschema import validate as json_schema_validator

from .reference import FolderReference, FileReference, references_from_string
from ..base.basemodel import BaseModel


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

    default: Any = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )

    spec: Dict = Field(
        None,
        description='An optional JSON Schema specification to validate the input value. '
        'You can use validate_spec method to validate a value against the spec.'
    )

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

        if v is not None:
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
