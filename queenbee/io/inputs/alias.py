"""Queenbee alias input types.

Use these alias inputs to create a different IO object for client side UIs. Alias inputs
provide a handler object to convert the input provided to alias to what is required with
the original input.

"""

import os
from typing import Dict, Union, List

from pydantic import constr, Field, validator
from jsonschema import validate as json_schema_validator

from ..common import ItemType, GenericInput, find_dup_items, IOAliasHandler
from ..artifact_source import HTTP, S3, ProjectFolder
from ...base.variable import validate_inputs_outputs_var_format, get_ref_variable


class DAGGenericInputAlias(GenericInput):
    """Base class for DAG Alias inputs.

    This class adds a handler to input to handle the process of loading the input
    from different graphical interfaces.
    """
    type: constr(regex='^DAGGenericInputAlias$') = 'DAGGenericInputAlias'

    platform: List[str] = Field(
        ...,
        description='Name of the client platform (e.g. Grasshopper, Revit, etc). The '
        'value can be any strings as long as it has been agreed between client-side '
        'developer and author of the recipe.'
    )

    handler: List[IOAliasHandler] = Field(
        ...,
        description='List of process actions to process the input or output value.'
    )

    default: str = Field(
        None,
        description='Default value for generic input.'
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

    @validator('platform', always=True)
    def create_empty_platform_list(cls, v):
        return [] if v is None else v

    @validator('handler', always=True)
    def check_duplicate_platform_name(cls, v, values):
        v = [] if v is None else v
        languages = [h.language for h in v]
        dup_lang = find_dup_items(languages)
        if dup_lang:
            raise ValueError(
                f'Duplicate use of language(s) found in alias handlers for '
                f'{values["platform"]}: {dup_lang}. Each language can only be used once '
                'in each platform.'
            )
        return v


class DAGLinkedInputAlias(DAGGenericInputAlias):
    """An Alias for Linked Inputs.

    A linked input alias will be hidden in the UI and will be linked to an object in 
    the UI using the input handler.
    """
    type: constr(regex='^DAGLinkedInputAlias$') = 'DAGLinkedInputAlias'


class DAGStringInputAlias(DAGGenericInputAlias):
    """An Alias String input.

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

    type: constr(regex='^DAGStringInputAlias$') = 'DAGStringInputAlias'

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


class DAGIntegerInputAlias(DAGGenericInputAlias):
    """An alias integer input.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/numeric.html#numeric
    for more information.

    """
    type: constr(regex='^DAGIntegerInputAlias$') = 'DAGIntegerInputAlias'

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


class DAGNumberInputAlias(DAGGenericInputAlias):
    """An alias number input.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/numeric.html#numeric
    for more information.
    """
    type: constr(regex='^DAGNumberInputAlias$') = 'DAGNumberInputAlias'

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


class DAGBooleanInputAlias(DAGGenericInputAlias):
    """The boolean type matches only two special values: True and False.

    Note that values that evaluate to true or false, such as 1 and 0, are not accepted.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/boolean.html for more
    information.
    """
    type: constr(regex='^DAGBooleanInputAlias$') = 'DAGBooleanInputAlias'

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


class DAGFolderInputAlias(DAGGenericInputAlias):
    """An alias folder input.

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
    type: constr(regex='^DAGFolderInputAlias$') = 'DAGFolderInputAlias'

    default: Union[HTTP, S3, ProjectFolder] = Field(
        None,
        description='The default source for file if the value is not provided.'
    )

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


class DAGFileInputAlias(DAGFolderInputAlias):
    """An alias file input.

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
    type: constr(regex='^DAGFileInputAlias$') = 'DAGFileInputAlias'

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


class DAGPathInputAlias(DAGFolderInputAlias):
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
    type: constr(regex='^DAGPathInputAlias$') = 'DAGPathInputAlias'

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


class DAGArrayInputAlias(DAGGenericInputAlias):
    """A JSON array input.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/array.html for
    more information.
    """
    type: constr(regex='^DAGArrayInputAlias$') = 'DAGArrayInputAlias'

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


class DAGJSONObjectInputAlias(DAGGenericInputAlias):
    """An alias JSON object input.

    JSON objects are similar to Python dictionaries.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/object.html for
    more information.
    """
    type: constr(regex='^DAGJSONObjectInputAlias$') = 'DAGJSONObjectInputAlias'

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


DAGAliasInputs = Union[
    DAGGenericInputAlias, DAGStringInputAlias, DAGIntegerInputAlias, DAGNumberInputAlias,
    DAGBooleanInputAlias, DAGFolderInputAlias, DAGFileInputAlias, DAGPathInputAlias,
    DAGArrayInputAlias, DAGJSONObjectInputAlias, DAGLinkedInputAlias
]
