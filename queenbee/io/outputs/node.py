"""Queenbee output types for status nodes.

For more information on plugins see plugin module.
"""

import os
import json
from typing import Union, List, Dict, Any
from pydantic import constr, Field, validator

from .function import FunctionStringOutput, FunctionIntegerOutput, \
    FunctionNumberOutput, FunctionBooleanOutput, FunctionFolderOutput, \
    FunctionFileOutput, FunctionPathOutput, FunctionArrayOutput, \
    FunctionJSONObjectOutput, FunctionOutputs

from .dag import DAGStringOutput, DAGIntegerOutput, DAGNumberOutput, \
    DAGBooleanOutput, DAGFolderOutput, DAGFileOutput, DAGPathOutput, \
    DAGArrayOutput, DAGJSONObjectOutput, DAGOutputs

from ..artifact_source import HTTP, S3, ProjectFolder


class NodeStringOutput(FunctionStringOutput):
    """A String output."""

    type: constr(regex='^NodeStringOutput$') = 'NodeStringOutput'

    value: str


class NodeIntegerOutput(FunctionIntegerOutput):
    """An integer output."""

    type: constr(regex='^NodeIntegerOutput$') = 'NodeIntegerOutput'

    value: int


class NodeNumberOutput(FunctionNumberOutput):
    """A number output."""

    type: constr(regex='^NodeNumberOutput$') = 'NodeNumberOutput'

    value: float


class NodeBooleanOutput(FunctionBooleanOutput):
    """The boolean type matches only two special values: True and False."""

    type: constr(regex='^NodeBooleanOutput$') = 'NodeBooleanOutput'

    value: bool


class NodeFolderOutput(FunctionFolderOutput):
    """A folder output."""
    type: constr(regex='^NodeFolderOutput$') = 'NodeFolderOutput'

    source: Union[HTTP, S3, ProjectFolder] = Field(
        ...,
        description='The path to source the file from.'
    )


class NodeFileOutput(FunctionFileOutput):
    """A file output."""

    type: constr(regex='^NodeFileOutput$') = 'NodeFileOutput'

    source: Union[HTTP, S3, ProjectFolder] = Field(
        ...,
        description='The path to source the file from.'
    )


class NodePathOutput(FunctionPathOutput):
    """A file or a folder output."""

    type: constr(regex='^NodePathOutput$') = 'NodePathOutput'

    source: Union[HTTP, S3, ProjectFolder] = Field(
        ...,
        description='The path to source the file from.'
    )


class NodeArrayOutput(FunctionArrayOutput):
    """An array output."""

    type: constr(regex='^NodeArrayOutput$') = 'NodeArrayOutput'

    value: List


class NodeJSONObjectOutput(FunctionJSONObjectOutput):
    """A JSON object output."""

    type: constr(regex='^NodeJSONObjectOutput$') = 'NodeJSONObjectOutput'

    value: Dict


NodeOutputs = Union[
    NodeStringOutput, NodeIntegerOutput, NodeNumberOutput,
    NodeBooleanOutput, NodeFolderOutput, NodeFileOutput, NodePathOutput,
    NodeArrayOutput, NodeJSONObjectOutput
]

def from_template(template: Union[DAGOutputs, FunctionOutputs], value: Any) -> NodeOutputs:
    """Generate a node output from a template output type and a value

    Args:
        template {Union[DAGOutputs, FunctionOutputs]} -- An output from a 
            template (DAG or Function)
        value {Any} -- The output value calculated for this template in 
            the workflow node

    Returns:
        NodeOutputs -- A Node Output object
    """

    template_dict = template.to_dict()
    del template_dict['type']

    if template.is_artifact:
        template_dict['source'] = value
    elif template.is_parameter:
        template_dict['value'] = value

    if template.__class__ in [DAGStringOutput, FunctionStringOutput]:
        return NodeStringOutput.parse_obj(template_dict)

    if template.__class__ in [DAGIntegerOutput, FunctionIntegerOutput]:
        return NodeIntegerOutput.parse_obj(template_dict)

    if template.__class__ in [DAGNumberOutput, FunctionNumberOutput]:
        return NodeNumberOutput.parse_obj(template_dict)

    if template.__class__ in [DAGBooleanOutput, FunctionBooleanOutput]:
        return NodeBooleanOutput.parse_obj(template_dict)

    if template.__class__ in [DAGFolderOutput, FunctionFolderOutput]:
        return NodeFolderOutput.parse_obj(template_dict)

    if template.__class__ in [DAGFileOutput, FunctionFileOutput]:
        return NodeFileOutput.parse_obj(template_dict)

    if template.__class__ in [DAGPathOutput, FunctionPathOutput]:
        return NodePathOutput.parse_obj(template_dict)

    if template.__class__ in [DAGArrayOutput, FunctionArrayOutput]:
        if isinstance(template_dict['value'], str):
            template_dict['value'] = json.loads(template_dict['value'])
        return NodeArrayOutput.parse_obj(template_dict)

    if template.__class__ in [DAGJSONObjectOutput, FunctionJSONObjectOutput]:
        if isinstance(template_dict['value'], str):
            template_dict['value'] = json.loads(template_dict['value'])
        return NodeJSONObjectOutput.parse_obj(template_dict)
