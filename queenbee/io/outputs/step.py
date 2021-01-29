"""Output types for a Queenbee Job steps.

For more information on plugins see plugin module.
"""

import json
from typing import Union, List, Dict, Any
from pydantic import constr, Field

from .function import FunctionStringOutput, FunctionIntegerOutput, \
    FunctionNumberOutput, FunctionBooleanOutput, FunctionFolderOutput, \
    FunctionFileOutput, FunctionPathOutput, FunctionArrayOutput, \
    FunctionJSONObjectOutput, FunctionOutputs

from .dag import DAGStringOutput, DAGIntegerOutput, DAGNumberOutput, \
    DAGBooleanOutput, DAGFolderOutput, DAGFileOutput, DAGPathOutput, \
    DAGArrayOutput, DAGJSONObjectOutput, DAGOutputs

from ..artifact_source import HTTP, S3, ProjectFolder


class StepStringOutput(FunctionStringOutput):
    """A String output."""

    type: constr(regex='^StepStringOutput$') = 'StepStringOutput'

    value: str


class StepIntegerOutput(FunctionIntegerOutput):
    """An integer output."""

    type: constr(regex='^StepIntegerOutput$') = 'StepIntegerOutput'

    value: int


class StepNumberOutput(FunctionNumberOutput):
    """A number output."""

    type: constr(regex='^StepNumberOutput$') = 'StepNumberOutput'

    value: float


class StepBooleanOutput(FunctionBooleanOutput):
    """The boolean type matches only two special values: True and False."""

    type: constr(regex='^StepBooleanOutput$') = 'StepBooleanOutput'

    value: bool


class StepFolderOutput(FunctionFolderOutput):
    """A folder output."""
    type: constr(regex='^StepFolderOutput$') = 'StepFolderOutput'

    source: Union[HTTP, S3, ProjectFolder] = Field(
        ...,
        description='The path to source the file from.'
    )


class StepFileOutput(FunctionFileOutput):
    """A file output."""

    type: constr(regex='^StepFileOutput$') = 'StepFileOutput'

    source: Union[HTTP, S3, ProjectFolder] = Field(
        ...,
        description='The path to source the file from.'
    )


class StepPathOutput(FunctionPathOutput):
    """A file or a folder output."""

    type: constr(regex='^StepPathOutput$') = 'StepPathOutput'

    source: Union[HTTP, S3, ProjectFolder] = Field(
        ...,
        description='The path to source the file from.'
    )


class StepArrayOutput(FunctionArrayOutput):
    """A JSON array output."""

    type: constr(regex='^StepArrayOutput$') = 'StepArrayOutput'

    value: List


class StepJSONObjectOutput(FunctionJSONObjectOutput):
    """A JSON object output."""

    type: constr(regex='^StepJSONObjectOutput$') = 'StepJSONObjectOutput'

    value: Dict


StepOutputs = Union[
    StepStringOutput, StepIntegerOutput, StepNumberOutput,
    StepBooleanOutput, StepFolderOutput, StepFileOutput, StepPathOutput,
    StepArrayOutput, StepJSONObjectOutput
]


def from_template(template: Union[DAGOutputs, FunctionOutputs], value: Any) -> StepOutputs:
    """Generate a step output from a template output type and a value

    Args:
        template {Union[DAGOutputs, FunctionOutputs]} -- An output from a
            template (DAG or Function)
        value {Any} -- The output value calculated for this template in
            the workflow step

    Returns:
        StepOutputs -- A Step Output object
    """

    template_dict = template.to_dict()
    del template_dict['type']

    if template.is_artifact:
        template_dict['source'] = value
    elif template.is_parameter:
        template_dict['value'] = value

    if template.__class__ in [DAGStringOutput, FunctionStringOutput]:
        return StepStringOutput.parse_obj(template_dict)

    if template.__class__ in [DAGIntegerOutput, FunctionIntegerOutput]:
        template_dict['value'] = int(float(template_dict['value']))
        return StepIntegerOutput.parse_obj(template_dict)

    if template.__class__ in [DAGNumberOutput, FunctionNumberOutput]:
        return StepNumberOutput.parse_obj(template_dict)

    if template.__class__ in [DAGBooleanOutput, FunctionBooleanOutput]:
        return StepBooleanOutput.parse_obj(template_dict)

    if template.__class__ in [DAGFolderOutput, FunctionFolderOutput]:
        return StepFolderOutput.parse_obj(template_dict)

    if template.__class__ in [DAGFileOutput, FunctionFileOutput]:
        return StepFileOutput.parse_obj(template_dict)

    if template.__class__ in [DAGPathOutput, FunctionPathOutput]:
        return StepPathOutput.parse_obj(template_dict)

    if template.__class__ in [DAGArrayOutput, FunctionArrayOutput]:
        if isinstance(template_dict['value'], str):
            template_dict['value'] = json.loads(template_dict['value'])
        return StepArrayOutput.parse_obj(template_dict)

    if template.__class__ in [DAGJSONObjectOutput, FunctionJSONObjectOutput]:
        if isinstance(template_dict['value'], str):
            template_dict['value'] = json.loads(template_dict['value'])
        try:
            # Try to parse JSON as a dict
            return StepJSONObjectOutput.parse_obj(template_dict)
        except:
            # Try to parse JSON as an array
            return StepArrayOutput.parse_obj(template_dict)
