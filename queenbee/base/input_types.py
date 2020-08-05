"""Queenbee input and output types.

The types and their properties are taken directly from the JSON schema definition and has
been modified to be used for Queenbee.
"""

import os
from typing import Dict, Union, List

from pydantic import constr, Field, validator
from jsonschema import validate as json_schema_validator

from .basemodel import BaseModel
from ..recipe.artifact_source import HTTPSource, S3Source, ProjectFolderSource


class BaseInput(BaseModel):
    """Base class for all input types."""

    name: str = Field(
        ...,
        description='Name is the input name.'
    )

    description: str = Field(
        None,
        description='Optional description for input.'
    )

    required: bool = Field(
        False,
        description='Whether this value must be specified.'
    )

    annotations: Dict = Field(
        None,
        description='An optional dictionary to add annotations to inputs. These '
        'annotations will be used by client side libraries to validate the inputs or '
        'bind them to specific actions. Use ``schema`` key for providing JSON Schema '
        'specifications for the input.'
    )

    @validator('annotations', always=True)
    def replace_none_value(cls, v):
        return {} if not v else v

    def validate(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        if 'schema' in self.annotations:
            json_schema_validator(value, self.annotations['schema'])
        return value


class StringInput(BaseInput):
    """A String input.

    You can add additional validation by defining a JSONSchema specification under
    annotations field and by using ``schema`` key.

    See http://json-schema.org/understanding-json-schema/reference/string.html#string for
    more information.

    .. code-block:: python

        "schema": {
            "type": "string",
            "maxLength": 50,
            "pattern": "(?i)(^.*\\.epw$)"
        }
    """
    type: constr(regex='^string$') = 'string'
    default: str = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )


class IntegerInput(BaseInput):
    """An integer input.

    You can add additional validation by defining a JSONSchema specification under
    annotations field and by using ``schema`` key.

    See http://json-schema.org/understanding-json-schema/reference/numeric.html#numeric
    for more information.
    """
    type: constr(regex='^integer$') = 'integer'
    default: int = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )

    def validate(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        value = int(value)
        return super(self).validate(value)


class NumberInput(BaseInput):
    """A number input.

    You can add additional validation by defining a JSONSchema specification under
    annotations field and by using ``schema`` key.

    See http://json-schema.org/understanding-json-schema/reference/numeric.html#numeric
    for more information.
    """
    type: constr(regex='^number$') = 'number'
    default: float = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )

    def validate(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        value = float(value)
        return super(self).validate(value)


class BooleanInput(BaseInput):
    """The boolean type matches only two special values: True and False.

    Note that values that evaluate to true or false, such as 1 and 0, are not accepted.

    You can add additional validation by defining a JSONSchema specification under
    annotations field and by using ``schema`` key.

    See http://json-schema.org/understanding-json-schema/reference/boolean.html for more
    information.
    """
    type: constr(regex='^boolean$') = 'boolean'
    default: bool = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )

    def validate(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        value = bool(value)
        return super(self).validate(value)


class FileInput(BaseInput):
    """A file input.

    File is a special string input. Unlike other string inputs, a file will be copied
    from its location to execution folder when a workflow is executed.

    You can add additional validation by defining a JSONSchema specification under
    annotations field and by using ``schema`` key.

    See http://json-schema.org/understanding-json-schema/reference/string.html#string for
    more information.

    .. code-block:: python

        "schema": {
            "type": "string",
            "maxLength": 50,
            "pattern": "(?i)(^.*\\.epw$)"
        }
    """
    type: constr(regex='^file$') = 'file'
    default: Union[HTTPSource, S3Source, ProjectFolderSource] = Field(
        None,
        description='The default source for file if the value is not provided.'
    )
    extension: str = Field(
        None,
        description='Optional extension for file. The check for extension is '
        'case-insensitive.'
    )

    def validate(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        value = str(value)
        assert os.path.isfile(value), f'There is no file at {value}'
        if self.extension:
            assert value.lower().endswith(self.extension.lower()), \
                f'Input file extension for {value} must be {self.extension}'
        return super(self).validate(value)


class FolderInput(BaseInput):
    """A folder input.

    Folder is a special string input. Unlike other string inputs, a folder will be copied
    from its location to execution folder when a workflow is executed.

    You can add additional validation by defining a JSONSchema specification under
    annotations field and by using ``schema`` key.

    See http://json-schema.org/understanding-json-schema/reference/string.html#string for
    more information.

    .. code-block:: python

        "schema": {
            "type": "string",
            "maxLength": 50,
        }
    """
    type: constr(regex='^folder$') = 'folder'
    default: Union[HTTPSource, S3Source, ProjectFolderSource] = Field(
        None,
        description='The default source for folder if the value is not provided.'
    )

    def validate(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        value = str(value)
        assert os.path.isdir(value), f'There is no folder at {value}'
        return super(self).validate(value)


class ObjectInput(BaseInput):
    """An object input.

    You can add additional validation by defining a JSONSchema specification under
    annotations field and by using ``schema`` key.

    See http://json-schema.org/understanding-json-schema/reference/object.html for
    more information.
    """
    type: constr(regex='^object$') = 'object'
    default: Dict = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )
    required: List[str] = Field(None, 'An optional list of required keys.')

    @validator('default', always=True)
    def replace_none_value(cls, v):
        return {} if not v else v


class ArrayInput(BaseInput):
    """An array input.

    You can add additional validation by defining a JSONSchema specification under
    annotations field and by using ``schema`` key.

    See http://json-schema.org/understanding-json-schema/reference/array.html for
    more information.
    """
    type: constr(regex='^array$') = 'array'
    default: List = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )
    items: Union[StringInput, IntegerInput, NumberInput, ObjectInput, 'ArrayInput'] = \
        Field(
            StringInput(),
            description='Type of items in the array. All the items in an array must be'
            ' from the same type.'
        )

    @validator('default', always=True)
    def replace_none_value(cls, v):
        return [] if not v else v


ArrayInput.update_forward_refs()
