"""common objects between different IO files."""
from enum import Enum
from typing import Dict, List, Any

from pydantic import constr, Field, validator
from jsonschema import validate as json_schema_validator

from .reference import FolderReference, FileReference, references_from_string
from ..base.basemodel import BaseModel


class ItemType(str, Enum):
    """Type enum for items in a list."""
    String = 'string'
    Integer = 'integer'
    Number = 'number'
    Boolean = 'boolean'
    Folder = 'folder'
    Array = 'array'
    Object = 'object'


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

    @property
    def required(self):
        """Check if input is required."""
        return True if not self.default else False

    spec: Dict = Field(
        None,
        description='An optional JSON Schema specification to validate the input value. '
        'You can use validate_spec method to validate a value against the spec.'
    )

    @validator('spec')
    def validate_default_value(cls, v, values):
        """Validate default value against spec if provided."""
        default = values['default']
        if default is not None:
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
    """Base class for all output types."""

    type: constr(regex='^GenericOutput$') = 'GenericOutput'

    name: str = Field(
        ...,
        description='Output name.'
    )

    description: str = Field(
        None,
        description='Optional description for output.'
    )

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

    @property
    def is_artifact(self):
        return False

    @property
    def is_parameter(self):
        return not self.is_artifact
