from typing import Dict, List, Union

from pydantic import Field, constr

from ..artifact_source import HTTP, S3, ProjectFolder
from ...base.basemodel import BaseModel
from ...base.parser import parse_file


class WorkflowArgument(BaseModel):
    """Workflow argument for parameter inputs that are not files or folders."""

    type: constr(regex='^WorkflowArgument$') = 'WorkflowArgument'

    name: str = Field(
        ...,
        description='Argument name. The name must match one of the input names from '
        'Workflow\'s DAG template.'
    )

    value: str = Field(
        ...,
        description='The value of the workflow argument.'
    )

    @property
    def is_artifact(self):
        return False

    @property
    def is_parameter(self):
        return not self.is_artifact


class WorkflowPathArgument(BaseModel):
    type: constr(regex='^WorkflowPathArgument$') = 'WorkflowPathArgument'

    name: str = Field(
        ...,
        description='Argument name. The name must match one of the input names from '
        'Workflow\'s template which can be a function or DAG.'
    )

    source: Union[HTTP, S3, ProjectFolder] = Field(
        ...,
        description='The path to source the file from.'
    )

    @property
    def is_artifact(self):
        return True

    @property
    def is_parameter(self):
        return not self.is_artifact


WorkflowArguments = Union[WorkflowArgument, WorkflowPathArgument]


def load_workflow_arguments(fp: str) -> List[WorkflowArguments]:
    """Load Workflow arguments from a JSON or YAML file.

    Args:
        fp: File path to a JSON or YAML file with a list of WorkflowArguments.

    Returns:
        List - A list of of WorkflowArgument and WorkflowPathArgument objects.
    """
    data = parse_file(fp)
    return load_workflow_arguments_from_dict(data)


def load_workflow_arguments_from_dict(data: List[Dict]) -> List[WorkflowArguments]:
    """Load Workflow arguments from a list of dictionaries.

    Args:
        data: A list of workflow arguments as dictionaries.

    Returns:
        List - A list of of WorkflowArgument and WorkflowPathArgument objects.
    """
    args = []
    for d in data:
        try:
            arg_type = d['type']
        except KeyError:
            raise ValueError(
                'Input argument with missing "type" key. Valid types are: '
                f'WorkflowArgument and WorkflowPathArgument:\n{d}'
            )
        if arg_type == 'WorkflowArgument':
            arg = WorkflowArgument.parse_obj(d)
        elif arg_type == 'WorkflowPathArgument':
            arg = WorkflowPathArgument.parse_obj(d)
        else:
            raise ValueError(
                f'Invalid type for Workflow argument: {arg_type}.'
                'Valid types are: WorkflowArgument and WorkflowPathArgument.'
            )
        args.append(arg)

    return args
