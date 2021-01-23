"""Queenbee input types for a DAG."""

import os
import warnings
from typing import Dict, Union, List

from pydantic import constr, Field, validator
from jsonschema import validate as json_schema_validator

from ..common import ItemType, GenericInput
from ..artifact_source import HTTP, S3, ProjectFolder
from .alias import DAGAliasInputs
from ...base.variable import validate_inputs_outputs_var_format, get_ref_variable


class DAGGenericInput(GenericInput):
    """Base class for DAG inputs.

    This class adds a handler to input to handle the process of loading the input
    from different graphical interfaces.
    """
    type: constr(regex='^DAGGenericInput$') = 'DAGGenericInput'

    default: str = Field(
        None,
        description='Default value for generic input.'
    )

    alias: List[DAGAliasInputs] = Field(
        None,
        description='A list of aliases for this input in different platforms.'
    )

    # see: https://github.com/ladybug-tools/queenbee/issues/172
    required: bool = Field(
        False,
        description='A field to indicate if this input is required. This input needs to '
        'be set explicitly even when a default value is provided.'
    )

    spec: Dict = Field(
        None,
        description='An optional JSON Schema specification to validate the input value. '
        'You can use validate_spec method to validate a value against the spec.'
    )

    def validate_spec(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        if self.spec:
            spec = dict(self.spec)
            json_schema_validator(value, spec)
        return value

    @validator('required', always=True)
    def check_required(cls, v, values):
        """Ensure required is set to True when default value is not provided."""
        default = values.get('default', None)
        name = values.get('name', None)
        if default is None and v is False:
            raise ValueError(
                f'{cls.__name__}.{name} -> required should be true if no default'
                f' is provided (default: {default}).'
            )
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

    @validator('alias', always=True)
    def create_empty_handler_list(cls, v):
        return [] if v is None else v


class DAGStringInput(DAGGenericInput):
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


class DAGIntegerInput(DAGGenericInput):
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


class DAGNumberInput(DAGGenericInput):
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
            spec['type'] = 'number'
            json_schema_validator(value, spec)
        return value


class DAGBooleanInput(DAGGenericInput):
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


class DAGFolderInput(DAGGenericInput):
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

    @validator('required', always=True)
    def check_required(cls, v, values):
        """Overwrite check_required fro artifacts to allow optional artifacts."""
        default = values.get('default', None)
        name = values.get('name', None)
        if default is None and v is False:
            warnings.warn(
                f'{cls.__name__}.{name} has no default value and is not required. '
                'Set to optional input artifact.'
            )
        return v

    def validate_spec(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        assert os.path.isdir(value), f'There is no folder at {value}'
        if self.spec:
            spec = dict(self.spec)
            spec['type'] = 'string'
            json_schema_validator(value, spec)

        return value

    @property
    def is_artifact(self):
        return True

    @property
    def is_optional(self):
        """A boolean that indicates if an artifact is optional."""
        return self.default is None and self.required is False


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

        return value


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


class DAGArrayInput(DAGGenericInput):
    """A JSON array input.

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


class DAGJSONObjectInput(DAGGenericInput):
    """A JSON object input.

    JSON objects are similar to Python dictionaries.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/object.html for
    more information.
    """
    type: constr(regex='^DAGJSONObjectInput$') = 'DAGJSONObjectInput'

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
    DAGGenericInput, DAGStringInput, DAGIntegerInput, DAGNumberInput, DAGBooleanInput,
    DAGFolderInput, DAGFileInput, DAGPathInput, DAGArrayInput, DAGJSONObjectInput
]
