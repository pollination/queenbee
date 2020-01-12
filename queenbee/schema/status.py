"""Queenbee Task Status class.

A task status keeps track of the outcome of a given workflow task.
"""

from datetime import datetime
from pydantic import Field, validator
from typing import List, Dict
from queenbee.schema.qutil import BaseModel
from queenbee.schema.arguments import Arguments
from queenbee.schema.operator import Operator


class BaseStatus(BaseModel):
    """Base Status model"""

    status: str = Field(
        ...,
        description='The status of this task. Can be "Running", "Succeeded", "Failed" or "Error"'
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
    """A Task Status"""

    id: str = Field(
        ...,
        description='The task unique ID'
    )

    name: str = Field(
        ...,
        description='A human readable name for the task. Usually defined by the \
            DAG task name but can be extended if the task is part of a loop for example. \
            This name is unique within the boundary of the DAG/Workflow that generated it.'
    )

    type: str = Field(
        ...,
        description='The type of task this status is for. Can be "Function", "DAG", "Workflow" or "Loop"'
    )

    template_ref: str = Field(
        ...,
        description='The name of the template that spawned this task'
    )

    operator: Operator = Field(
        None,
        description='The operator used to run this task. Only applies to Function tasks.'
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
        description='A list of the last tasks to ran in the context of this \
            task. In the case of a DAG or a workflow this will be the last task that has \
            been executed. It will remain empty for functions.'
    )

    @validator('type')
    def check_config(cls, v,):
        assert v in ['Function', 'DAG', 'Workflow',
                     'Loop'], "Type must be one of Function, DAG, Workflow or Loop"
        return v


class WorkflowStatus(BaseStatus):
    """Workflow Status"""

    id: str = Field(
        ...,
        description='The ID of the individual workflow run.'
    )

    tasks: Dict[str, TaskStatus] = {}
