"""Queenbee output types for functions.

For more information on plugins see plugin module.
"""

from typing import Union
from pydantic import constr, Field

from ..common import PathOutput, ItemType


class FunctionFileOutput(PathOutput):
    """Function File output."""
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
    """Function Folder output."""
    type: constr(regex='^FunctionFolderOutput$') = 'FunctionFolderOutput'

    path: str = Field(
        ...,
        description='Path to the output folder relative to where the function command '
        'is executed.'
        )

    @property
    def is_artifact(self):
        return True


class FunctionPathOutput(PathOutput):
    """Function Path output."""
    type: constr(regex='^FunctionPathOutput$') = 'FunctionPathOutput'

    path: str = Field(
        ...,
        description='Path to the output file or folder relative to where the function '
        'command is executed.'
        )

    @property
    def is_artifact(self):
        return True


class FunctionStringOutput(FunctionFileOutput):
    """Function string output.

    This output loads the content from a file as a string.
    """
    type: constr(regex='^FunctionStringOutput$') = 'FunctionStringOutput'

    @property
    def is_artifact(self):
        return False


class FunctionIntegerOutput(FunctionStringOutput):
    """Function integer output.

    This output loads the content from a file as an integer.
    """
    type: constr(regex='^FunctionIntegerOutput$') = 'FunctionIntegerOutput'


class FunctionNumberOutput(FunctionStringOutput):
    """Function number output.

    This output loads the content from a file as a floating number.
    """
    type: constr(regex='^FunctionNumberOutput$') = 'FunctionNumberOutput'


class FunctionBooleanOutput(FunctionStringOutput):
    """Function boolean output.

    This output loads the content from a file as a boolean.
    """
    type: constr(regex='^FunctionBooleanOutput$') = 'FunctionBooleanOutput'


class FunctionArrayOutput(FunctionStringOutput):
    """Function array output.

    This output loads the content from a JSON file which must be a JSON Array.
    """
    type: constr(regex='^FunctionArrayOutput$') = 'FunctionArrayOutput'

    items_type: ItemType = Field(
        ItemType.String,
        description='Type of items in this array. All the items in an array must be '
        'from the same type.'
    )


class FunctionJSONObjectOutput(FunctionStringOutput):
    """Function object output.

    This output loads the content from a file as a JSON object.
    """
    type: constr(regex='^FunctionJSONObjectOutput$') = 'FunctionJSONObjectOutput'


FunctionOutputs = Union[
    FunctionStringOutput, FunctionIntegerOutput, FunctionNumberOutput,
    FunctionBooleanOutput, FunctionFolderOutput, FunctionFileOutput, FunctionPathOutput,
    FunctionArrayOutput, FunctionJSONObjectOutput
]
