"""Queenbee input and output types for a DAG."""

import os
from typing import Dict, Union, List

from pydantic import constr, Field, validator
from jsonschema import validate as json_schema_validator

from .common import ItemType, GenericInput, FromOutput
from ..recipe.artifact_source import HTTP, S3, ProjectFolder
from ..io.reference import FileReference, FolderReference, TaskReference


class DAGStringInput(GenericInput):
    """A String input.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/string.html#string for
    more information.

    .. code-block:: python

        "schema": {
            "type": "string",
            "maxLength": 50,
            "pattern": "(?i)(^.*\\.epw$)"
        }

    """

    type: constr(regex='^DAGStringInput$') = 'DAGStringInput'

    default: str = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )

    def validate_spec(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        if self.spec:
            spec = dict(self.spec)
            spec['type'] = 'string'
            json_schema_validator(value, spec)
        return value


class DAGIntegerInput(GenericInput):
    """An integer input.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/numeric.html#numeric
    for more information.

    """
    type: constr(regex='^DAGIntegerInput$') = 'DAGIntegerInput'

    default: int = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )

    def validate_spec(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        if self.spec:
            spec = dict(self.spec)
            spec['type'] = 'integer'
            json_schema_validator(value, spec)
        return value


class DAGNumberInput(GenericInput):
    """A number input.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/numeric.html#numeric
    for more information.
    """
    type: constr(regex='^DAGNumberInput$') = 'DAGNumberInput'

    default: float = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )

    def validate_spec(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        if self.spec:
            spec = dict(self.spec)
            spec['type'] = 'integer'
            json_schema_validator(value, spec)
        return value


class DAGBooleanInput(GenericInput):
    """The boolean type matches only two special values: True and False.

    Note that values that evaluate to true or false, such as 1 and 0, are not accepted.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/boolean.html for more
    information.
    """
    type: constr(regex='^DAGBooleanInput$') = 'DAGBooleanInput'

    default: bool = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )

    def validate_spec(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        if self.spec:
            spec = dict(self.spec)
            spec['type'] = 'boolean'
            json_schema_validator(value, spec)
        return value


class DAGFolderInput(GenericInput):
    """A folder input.

    Folder is a special string input. Unlike other string inputs, a folder will be copied
    from its location to execution folder when a workflow is executed.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/string.html#string for
    more information.

    .. code-block:: python

        "schema": {
            "type": "string",
            "maxLength": 50,
        }
    """
    type: constr(regex='^DAGFolderInput$') = 'DAGFolderInput'

    default: Union[HTTP, S3, ProjectFolder] = Field(
        None,
        description='The default source for file if the value is not provided.'
    )

    def validate_spec(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        # TODO: This should only be checked for input folders
        assert os.path.isdir(value), f'There is no folder at {value}'
        if self.spec:
            spec = dict(self.spec)
            spec['type'] = 'string'
            json_schema_validator(value, spec)

    @property
    def is_artifact(self):
               return True


class DAGFileInput(DAGFolderInput):
    """A file input.

    File is a special string input. Unlike other string inputs, a file will be copied
    from its location to execution folder when a workflow is executed.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/string.html#string for
    more information.

    .. code-block:: python

        # a file with maximum 50 characters with an ``epw`` extension.

        "schema": {
            "type": "string",
            "maxLength": 50,
            "pattern": "(?i)(^.*\\.epw$)"
        }

    """
    type: constr(regex='^DAGFileInput$') = 'DAGFileInput'

    extensions: List[str] = Field(
        None,
        description='Optional list of extensions for file. The check for extension is '
        'case-insensitive.'
    )

    def validate_spec(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        assert os.path.isfile(value), f'There is no file at {value}'
        if self.extensions:
            assert value.lower().endswith(self.extension.lower()), \
                f'Input file extension for {value} must be {self.extensions}'
        if self.spec:
            spec = dict(self.spec)
            spec['type'] = 'string'
            json_schema_validator(value, spec)


class DAGPathInput(DAGFolderInput):
    """A file or a folder input.

    Use this input only in cases that the input can be either a file or folder. For file
    or folder-only inputs see File and Folder.

    Path is a special string input. Unlike other string inputs, a path will be copied
    from its location to execution folder when a workflow is executed.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/string.html#string for
    more information.

    .. code-block:: python

        # a file with maximum 50 characters with an ``epw`` extension.

        "schema": {
            "type": "string",
            "maxLength": 50,
            "pattern": "(?i)(^.*\\.epw$)"
        }

    """
    type: constr(regex='^DAGPathInput$') = 'DAGPathInput'

    extensions: List[str] = Field(
        None,
        description='Optional list of extensions for path. The check for extension is '
        'case-insensitive. The extension will only be validated for file inputs.'
    )

    def validate_spec(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        if os.path.isfile(value):
            if self.extensions:
                assert value.lower().endswith(self.extension.lower()), \
                    f'Input file extension for {value} must be {self.extensions}'
        elif not os.path.isdir(value):
            raise ValueError(f'{value} is not a valid file or folder.')

        if self.spec:
            spec = dict(self.spec)
            spec['type'] = 'string'
            json_schema_validator(value, spec)


class DAGArrayInput(GenericInput):
    """An array input.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/array.html for
    more information.
    """
    type: constr(regex='^DAGArrayInput$') = 'DAGArrayInput'

    default: List = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )

    items_type: ItemType = Field(
        ItemType.String,
        description='Type of items in an array. All the items in an array must be from '
        'the same type.'
    )

    @validator('default', always=True)
    def replace_none_value(cls, v):
        return [] if not v else v

    def validate_spec(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        if self.spec:
            spec = dict(self.spec)
            spec['type'] = 'array'
            spec['items'] = self.items_type.lower()
            json_schema_validator(value, spec)


class DAGObjectInput(GenericInput):
    """A JSON object input.

    JSON objects are similar to Python dictionaries.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/object.html for
    more information.
    """
    type: constr(regex='^DAGObjectInput$') = 'DAGObjectInput'

    default: Dict = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )

    @validator('default', always=True)
    def replace_none_value(cls, v):
        return {} if not v else v

    def validate_spec(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        if self.spec:
            spec = dict(self.spec)
            spec['type'] = 'object'
            json_schema_validator(value, spec)


DAGInputs = Union[
    GenericInput, DAGStringInput, DAGIntegerInput, DAGNumberInput, DAGBooleanInput,
    DAGFolderInput, DAGFileInput, DAGPathInput, DAGArrayInput, DAGObjectInput]


class DAGFileOutput(FromOutput):
    """DAG file output."""
    type: constr(regex='^DAGFileOutput$') = 'DAGFileOutput'

    from_: Union[TaskReference, FileReference] = Field(
        ...,
        description='Reference to a file or a task output. Task output must be file.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGFolderOutput(FromOutput):
    """DAG folder output."""
    type: constr(regex='^DAGFolderOutput$') = 'DAGFolderOutput'

    from_: Union[TaskReference, FolderReference] = Field(
        ...,
        description='Reference to a folder or a task output. Task output must be folder.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGStringOutput(DAGFileOutput):
    """DAG string output.

    This output loads the content from a file as a string.
    """
    type: constr(regex='^DAGStringOutput$') = 'DAGStringOutput'

    @property
    def is_artifact(self):
        return False


class DAGObjectOutput(DAGFileOutput):
    """DAG string output.

    This output loads the content from a file as a JSON object.
    """
    type: constr(regex='^DAGObjectOutput$') = 'DAGObjectOutput'

    @property
    def is_artifact(self):
        return False


DAGOutputs = Union[DAGFileOutput, DAGFolderOutput, DAGStringOutput, DAGObjectOutput]
