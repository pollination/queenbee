"""Queenbee input and output types for functions.

    For more information on operators see operator module.

"""

import os
from typing import Union, List
from pydantic import constr, Field
from jsonschema import validate as json_schema_validator

from .common import GenericInput, PathOutput
from .dag import DAGStringInput, DAGIntegerInput, DAGNumberInput, DAGBooleanInput, \
    DAGFolderInput, DAGArrayInput, DAGObjectInput


class FunctionStringInput(DAGStringInput):
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


class FunctionIntegerInput(DAGIntegerInput):
    """An integer input.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/numeric.html#numeric
    for more information.

    """
    type: constr(regex='^FunctionIntegerInput$') = 'FunctionIntegerInput'


class FunctionNumberInput(DAGNumberInput):
    """A number input.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/numeric.html#numeric
    for more information.
    """
    type: constr(regex='^FunctionNumberInput$') = 'FunctionNumberInput'


class FunctionBooleanInput(DAGBooleanInput):
    """The boolean type matches only two special values: True and False.

    Note that values that evaluate to true or false, such as 1 and 0, are not accepted.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/boolean.html for more
    information.
    """
    type: constr(regex='^FunctionBooleanInput$') = 'FunctionBooleanInput'


class FunctionFolderInput(DAGFolderInput):
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
    type: constr(regex='^FunctionFolderInput$') = 'FunctionFolderInput'

    # TODO: Change this path to target_path and the one for output to source_path
    # for this iteration I'm keeping the changes as minimum as possible to break as
    # little as possible.
    path: str = Field(
        ...,
        description='Path to the target location that the input will be copied to. '
        ' This path is relative to the working directory where the command is executed.'
    )


class FunctionFileInput(FunctionFolderInput):
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
    type: constr(regex='^FunctionFileInput$') = 'FunctionFileInput'

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


class FunctionPathInput(FunctionFileInput):
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
    type: constr(regex='^FunctionPathInput$') = 'FunctionPathInput'

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


class FunctionArrayInput(DAGArrayInput):
    """An array input.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/array.html for
    more information.
    """
    type: constr(regex='^FunctionArrayInput$') = 'FunctionArrayInput'


class FunctionObjectInput(DAGObjectInput):
    """A JSON object input.

    JSON objects are similar to Python dictionaries.

    You can add additional validation by defining a JSONSchema specification.

    See http://json-schema.org/understanding-json-schema/reference/object.html for
    more information.
    """
    type: constr(regex='^FunctionObjectInput$') = 'FunctionObjectInput'


FunctionInputs = Union[
    GenericInput, FunctionStringInput, FunctionIntegerInput, FunctionNumberInput,
    FunctionBooleanInput, FunctionFolderInput, FunctionFileInput, FunctionPathInput,
    FunctionArrayInput, FunctionObjectInput
]


# function outputs
class FunctionFileOutput(PathOutput):

    type: constr(regex='^FunctionFileOutput$') = 'FunctionFileOutput'

    path: str = Field(
        ...,
        description='Path to the output file relative to where the function command '
        'is executed.'
        )

    @property
    def is_artifact(self):
        return True


class FunctionFolderOutput(PathOutput):

    type: constr(regex='^FunctionFolderOutput$') = 'FunctionFolderOutput'

    path: str = Field(
        ...,
        description='Path to the output folder relative to where the function command '
        'is executed.'
        )

    @property
    def is_artifact(self):
        return True


class FunctionStringOutput(FunctionFileOutput):

    type: constr(regex='^FunctionStringOutput$') = 'FunctionStringOutput'

    @property
    def is_artifact(self):
        return False


class FunctionObjectOutput(FunctionFileOutput):

    type: constr(regex='^FunctionObjectOutput$') = 'FunctionObjectOutput'

    @property
    def is_artifact(self):
        return False


FunctionOutputs = Union[
    FunctionFileOutput, FunctionFolderOutput, FunctionStringOutput, FunctionObjectOutput]
