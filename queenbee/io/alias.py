"""Queenbee alias input and output types.

Use these alias inputs and outputs to create a different IO object for client side UIs.
Alias inputs provide a handler object to convert the input provided to alias to what is
required with the original input.
"""

import os
from typing import Dict, Union, List

from pydantic import constr, Field, validator
from jsonschema import validate as json_schema_validator

from .common import ItemType, GenericInput, FromOutput, find_dup_items
from .artifact_source import HTTP, S3, ProjectFolder
from ..io.reference import FileReference, FolderReference, TaskReference
from ..base.basemodel import BaseModel


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
    """An array input.

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
    DAGArrayInputAlias, DAGJSONObjectInputAlias
]


class DAGGenericOutputAlias(FromOutput):
    """DAG generic alias output.

    In most cases, you should not be using the generic output unless you need a dynamic
    output that changes its type in different platforms because of returning different
    objects in handler.
    """
    type: constr(regex='^DAGGenericOutputAlias$') = 'DAGGenericOutputAlias'

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


class DAGFileOutputAlias(DAGGenericOutputAlias):
    """DAG alias file output."""
    type: constr(regex='^DAGFileOutputAlias$') = 'DAGFileOutputAlias'

    from_: Union[TaskReference, FileReference] = Field(
        ...,
        description='Reference to a file or a task output. Task output must be file.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGFolderOutputAlias(DAGGenericOutputAlias):
    """DAG alias folder output."""
    type: constr(regex='^DAGFolderOutputAlias$') = 'DAGFolderOutputAlias'

    from_: Union[TaskReference, FolderReference] = Field(
        ...,
        description='Reference to a folder or a task output. Task output must be folder.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGPathOutputAlias(DAGGenericOutputAlias):
    """DAG alias path output."""
    type: constr(regex='^DAGPathOutputAlias$') = 'DAGPathOutputAlias'

    from_: Union[TaskReference, FileReference, FolderReference] = Field(
        ...,
        description='Reference to a file, folder or a task output. Task output must '
        'either be a file or a folder.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGStringOutputAlias(DAGFileOutputAlias):
    """DAG alias string output.

    This output loads the content from a file as a string.
    """
    type: constr(regex='^DAGStringOutputAlias$') = 'DAGStringOutputAlias'

    @property
    def is_artifact(self):
        return False


class DAGIntegerOutputAlias(DAGStringOutputAlias):
    """DAG alias integer output.

    This output loads the content from a file as an integer.
    """
    type: constr(regex='^DAGIntegerOutputAlias$') = 'DAGIntegerOutputAlias'


class DAGNumberOutputAlias(DAGStringOutputAlias):
    """DAG alias number output.

    This output loads the content from a file as a floating number.
    """
    type: constr(regex='^DAGNumberOutputAlias$') = 'DAGNumberOutputAlias'


class DAGBooleanOutputAlias(DAGStringOutputAlias):
    """DAG alias boolean output.

    This output loads the content from a file as a boolean.
    """
    type: constr(regex='^DAGBooleanOutputAlias$') = 'DAGBooleanOutputAlias'


class DAGArrayOutputAlias(DAGStringOutputAlias):
    """DAG alias array output.

    This output loads the content from a JSON file which must be a JSON Array.
    """
    type: constr(regex='^DAGArrayOutputAlias$') = 'DAGArrayOutputAlias'

    items_type: ItemType = Field(
        ItemType.String,
        description='Type of items in this array. All the items in an array must be '
        'from the same type.'
    )


class DAGJSONObjectOutputAlias(DAGStringOutputAlias):
    """DAG alias object output.

    This output loads the content from a file as a JSON object.
    """
    type: constr(regex='^DAGJSONObjectOutputAlias$') = 'DAGJSONObjectOutputAlias'


DAGAliasOutputs = Union[
    DAGGenericOutputAlias, DAGStringOutputAlias, DAGIntegerOutputAlias,
    DAGNumberOutputAlias, DAGBooleanOutputAlias, DAGFolderOutputAlias,
    DAGFileOutputAlias, DAGPathOutputAlias, DAGArrayOutputAlias, DAGJSONObjectOutputAlias
]
