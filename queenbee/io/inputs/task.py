"""Argument and Return objects for tasks.

Task argument and return objects provide the interface to connect:

 * DAG inputs to function inputs
 * DAG inputs to DAG inputs  -- for nested DAGs
 * function outputs to following function inputs
 * function outputs to DAG outputs
 * DAG outputs to DAG outputs  -- for nested DAGs

"""

from typing import Union
from pydantic import Field, constr
from ...base.basemodel import BaseModel
from ..reference import InputReference, ItemReference, TaskReference, ValueReference, \
    InputFileReference, InputFolderReference, InputPathReference, \
    TaskFileReference, TaskFolderReference, TaskPathReference, \
    ValueFileReference, ValueFolderReference


class TaskArgument(BaseModel):
    """Task argument for receiving inputs that are not files or folders."""

    type: constr(regex='^TaskArgument$') = 'TaskArgument'

    name: str = Field(
        ...,
        description='Argument name. The name must match one of the input names from '
        'Task\'s template which can be a function or DAG.'
    )

    from_: Union[InputReference, TaskReference, ItemReference, ValueReference] = Field(
        ...,
        description='A reference to a DAG input, a DAG output or another task output.'
        ' You can also use the ValueReference type to hard-code an input value.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return False

    @property
    def is_parameter(self):
        return not self.is_artifact


class TaskPathArgument(BaseModel):
    type: constr(regex='^TaskPathArgument$') = 'TaskPathArgument'

    name: str = Field(
        ...,
        description='Argument name. The name must match one of the input names from '
        'Task\'s template which can be a function or DAG.'
    )

    from_: Union[
        InputFileReference, InputFolderReference, InputPathReference,
        TaskFileReference, TaskFolderReference, TaskPathReference,
        ValueFileReference, ValueFolderReference
            ] = Field(
        ...,
        description='A reference to a DAG input, a DAG output or another task output.'
        ' You can also use the ValueReference type to hard-code an input value.',
        alias='from'
    )

    sub_path: str = Field(
        None,
        description='A sub_path inside the path that is provided in the ``from`` field.'
        ' Use sub_path to only access part of the Path that is needed instead of'
        ' copying all the files and folders inside the path.'
    )

    @property
    def is_artifact(self):
        return True

    @property
    def is_parameter(self):
        return not self.is_artifact


TaskArguments = Union[TaskArgument, TaskPathArgument]
