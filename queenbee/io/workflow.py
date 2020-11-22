from typing import Union

from pydantic import Field, constr

from .artifact_source import HTTP, S3, ProjectFolder
from ..base.basemodel import BaseModel


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

    value: Union[HTTP, S3, ProjectFolder] = Field(
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
