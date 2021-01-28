"""Input types for Queenbee job steps.

For more information on plugins see plugin module.
"""

import json
from typing import Union, List, Dict, Any
from pydantic import constr, Field

from .function import FunctionStringInput, FunctionIntegerInput, \
    FunctionNumberInput, FunctionBooleanInput, FunctionFolderInput, \
    FunctionFileInput, FunctionPathInput, FunctionArrayInput, \
    FunctionJSONObjectInput, FunctionInputs

from .dag import DAGStringInput, DAGIntegerInput, DAGNumberInput, \
    DAGBooleanInput, DAGFolderInput, DAGFileInput, DAGPathInput, \
    DAGArrayInput, DAGJSONObjectInput, DAGInputs

from ..artifact_source import HTTP, S3, ProjectFolder


class StepStringInput(FunctionStringInput):
    """A String input."""

    type: constr(regex='^StepStringInput$') = 'StepStringInput'

    value: str


class StepIntegerInput(FunctionIntegerInput):
    """An integer input."""

    type: constr(regex='^StepIntegerInput$') = 'StepIntegerInput'

    value: int


class StepNumberInput(FunctionNumberInput):
    """A number input."""

    type: constr(regex='^StepNumberInput$') = 'StepNumberInput'

    value: float


class StepBooleanInput(FunctionBooleanInput):
    """The boolean type matches only two special values: True and False."""

    type: constr(regex='^StepBooleanInput$') = 'StepBooleanInput'

    value: bool


class StepFolderInput(FunctionFolderInput):
    """A folder input."""
    type: constr(regex='^StepFolderInput$') = 'StepFolderInput'

    source: Union[HTTP, S3, ProjectFolder] = Field(
        ...,
        description='The path to source the file from.'
    )

    # TODO: Change this path to target_path and the one for output to source_path
    # for this iteration I'm keeping the changes as minimum as possible to break as
    # little as possible.
    path: str = Field(
        None,
        description='Path to the target location that the input will be copied to. '
        ' This path is relative to the working directory where the command is executed.'
    )


class StepFileInput(FunctionFileInput):
    """A file input."""

    type: constr(regex='^StepFileInput$') = 'StepFileInput'

    source: Union[HTTP, S3, ProjectFolder] = Field(
        ...,
        description='The path to source the file from.'
    )

    # TODO: Change this path to target_path and the one for output to source_path
    # for this iteration I'm keeping the changes as minimum as possible to break as
    # little as possible.
    path: str = Field(
        None,
        description='Path to the target location that the input will be copied to. '
        ' This path is relative to the working directory where the command is executed.'
    )


class StepPathInput(FunctionPathInput):
    """A file or a folder input."""

    type: constr(regex='^StepPathInput$') = 'StepPathInput'

    source: Union[HTTP, S3, ProjectFolder] = Field(
        ...,
        description='The path to source the file from.'
    )

    # TODO: Change this path to target_path and the one for output to source_path
    # for this iteration I'm keeping the changes as minimum as possible to break as
    # little as possible.
    path: str = Field(
        None,
        description='Path to the target location that the input will be copied to. '
        ' This path is relative to the working directory where the command is executed.'
    )


class StepArrayInput(FunctionArrayInput):
    """A JSON array input."""

    type: constr(regex='^StepArrayInput$') = 'StepArrayInput'

    value: List


class StepJSONObjectInput(FunctionJSONObjectInput):
    """A JSON object input."""

    type: constr(regex='^StepJSONObjectInput$') = 'StepJSONObjectInput'

    value: Dict


StepInputs = Union[
    StepStringInput, StepIntegerInput, StepNumberInput,
    StepBooleanInput, StepFolderInput, StepFileInput, StepPathInput,
    StepArrayInput, StepJSONObjectInput
]


def from_template(template: Union[DAGInputs, FunctionInputs], value: Any) -> StepInputs:
    """Generate a step input from a template input type and a value

    Args:
        template {Union[DAGInputs, FunctionInputs]} -- An input from a
            template (DAG or Function)
        value {Any} -- The input value calculated for this template in
            the workflow step

    Returns:
        StepInputs -- A Step Input object
    """

    template_dict = template.to_dict()
    del template_dict['type']

    if template.is_artifact:
        template_dict['source'] = value
    elif template.is_parameter:
        template_dict['value'] = value

    if template.__class__ in [DAGStringInput, FunctionStringInput]:
        return StepStringInput.parse_obj(template_dict)

    if template.__class__ in [DAGIntegerInput, FunctionIntegerInput]:
        template_dict['value'] = int(float(template_dict['value']))
        return StepIntegerInput.parse_obj(template_dict)

    if template.__class__ in [DAGNumberInput, FunctionNumberInput]:
        return StepNumberInput.parse_obj(template_dict)

    if template.__class__ in [DAGBooleanInput, FunctionBooleanInput]:
        return StepBooleanInput.parse_obj(template_dict)

    if template.__class__ in [DAGFolderInput, FunctionFolderInput]:
        return StepFolderInput.parse_obj(template_dict)

    if template.__class__ in [DAGFileInput, FunctionFileInput]:
        return StepFileInput.parse_obj(template_dict)

    if template.__class__ in [DAGPathInput, FunctionPathInput]:
        return StepPathInput.parse_obj(template_dict)

    if template.__class__ in [DAGArrayInput, FunctionArrayInput]:
        if isinstance(template_dict['value'], str):
            template_dict['value'] = json.loads(template_dict['value'])
        return StepArrayInput.parse_obj(template_dict)

    if template.__class__ in [DAGJSONObjectInput, FunctionJSONObjectInput]:
        if isinstance(template_dict['value'], str):
            template_dict['value'] = json.loads(template_dict['value'])
        return StepJSONObjectInput.parse_obj(template_dict)
