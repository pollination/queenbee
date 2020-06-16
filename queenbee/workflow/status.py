"""Queenbee Task Status class.

A task status keeps track of the outcome of a given workflow task.
"""
from enum import Enum
from datetime import datetime
from pydantic import Field
from typing import List, Dict

from ..base.basemodel import BaseModel
from .arguments import Arguments


class StatusType(str, Enum):

    Function = 'function'

    DAG = 'dag'

    Loop = 'loop'


class BaseStatus(BaseModel):
    """Base Status model"""

    status: str = Field(
        ...,
        description='The status of this task. Can be "Running", "Succeeded", "Failed" '
        'or "Error"'
    )

    message: str = Field(
        None,
        description='Any message produced by the task. Usually error/debugging hints.'
    )

    started_at: datetime = Field(
        ...,
        description='The time at which the task was started'
    )

    finished_at: datetime = Field(
        None,
        description='The time at which the task was completed'
    )


class TaskStatus(BaseStatus):
    """The Status of a Workflow Task"""

    id: str = Field(
        ...,
        description='The task unique ID'
    )

    name: str = Field(
        ...,
        description='A human readable name for the task. Usually defined by the '
        'DAG task name but can be extended if the task is part of a loop for example. '
        'This name is unique within the boundary of the DAG/Workflow that generated it.'
    )

    type: StatusType = Field(
        ...,
        description='The type of task this status is for. Can be "function", "dag" or '
        '"loop"'
    )

    template_ref: str = Field(
        ...,
        description='The name of the template that spawned this task'
    )

    command: str = Field(
        None,
        description='The command used to run this task. Only applies to Function tasks.'
    )

    inputs: Arguments = Field(
        ...,
        description='The inputs used by this task'
    )

    outputs: Arguments = Field(
        ...,
        description='The outputs produced by this task'
    )

    boundary_id: str = Field(
        None,
        description='This indicates the task ID of the associated template root \
            task in which this task belongs to. A DAG task will have the id of the \
            parent DAG for example.'
    )

    children: List[str] = Field(
        ...,
        description='A list of child task IDs'
    )

    outbound_tasks: List[str] = Field(
        ...,
        description='A list of the last tasks to ran in the context of this '
        'task. In the case of a DAG or a workflow this will be the last task that has '
        'been executed. It will remain empty for functions.'
    )


class WorkflowStatus(BaseStatus):
    """Workflow Status"""

    id: str = Field(
        ...,
        description='The ID of the individual workflow run.'
    )

    entrypoint: str = Field(
        None,
        description='The ID of the first task in the workflow'
    )

    tasks: Dict[str, TaskStatus] = {}
