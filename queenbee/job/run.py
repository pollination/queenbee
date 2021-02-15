"""Queenbee run class.

A Run contains the status of an individual recipe being executed
"""
from enum import Enum
from datetime import datetime
from pydantic import Field, constr
from typing import List, Dict, Union

from ..base.basemodel import BaseModel
from ..io.common import IOBase
from ..io.inputs.step import StepStringInput, StepInputs
from ..io.outputs.step import StepOutputs
from .status import BaseStatus


class StatusType(str, Enum):
    """Type enum for status type."""
    Function = 'Function'

    DAG = 'DAG'

    Loop = 'Loop'

    Unknown = 'Unknown'


class StepStatus(BaseStatus):
    """The Status of a Job Step"""
    type: constr(regex='^StepStatus$') = 'StepStatus'

    id: str = Field(
        ...,
        description='The step unique ID'
    )

    name: str = Field(
        ...,
        description='A human readable name for the step. Usually defined by the '
        'DAG task name but can be extended if the step is part of a loop for example. '
        'This name is unique within the boundary of the DAG/Job that generated it.'
    )

    status_type: StatusType = Field(
        ...,
        description='The type of step this status is for. Can be "Function", "DAG" or '
        '"Loop"'
    )

    template_ref: str = Field(
        ...,
        description='The name of the template that spawned this step'
    )

    command: str = Field(
        None,
        description='The command used to run this step. Only applies to Function steps.'
    )

    inputs: List[StepInputs] = Field(
        ...,
        description='The inputs used by this step.'
    )

    outputs: List[StepOutputs] = Field(
        ...,
        description='The outputs produced by this step.'
    )

    boundary_id: str = Field(
        None,
        description='This indicates the step ID of the associated template root \
            step in which this step belongs to. A DAG step will have the id of the \
            parent DAG for example.'
    )

    children_ids: List[str] = Field(
        ...,
        description='A list of child step IDs'
    )

    outbound_steps: List[str] = Field(
        ...,
        description='A list of the last step to ran in the context of this '
        'step. In the case of a DAG or a job this will be the last step that has '
        'been executed. It will remain empty for functions.'
    )


class RunStatus(BaseStatus):
    """Job Status."""
    api_version: constr(regex='^v1beta1$') = Field('v1beta1', readOnly=True)

    type: constr(regex='^RunStatus$') = 'RunStatus'

    id: str = Field(
        ...,
        description='The ID of the individual run.'
    )

    job_id: str = Field(
        ...,
        description='The ID of the job that generated this run'
    )

    entrypoint: str = Field(
        None,
        description='The ID of the first step in the run.'
    )

    steps: Dict[str, StepStatus] = {}

    inputs: List[StepInputs] = Field(
        ...,
        description='The inputs used for this run.'
    )

    outputs: List[StepOutputs] = Field(
        ...,
        description='The outputs produced by this run.'
    )
