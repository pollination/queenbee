"""Queenbee Simulation step status class.

A step status keeps track of the outcome of a given simulation step.
"""
from enum import Enum
from datetime import datetime
from pydantic import Field, constr
from typing import List, Dict

from ..io.common import IOBase
from ..io.inputs.step import StepInputs
from ..io.outputs.step import StepOutputs


class StatusType(str, Enum):
    """Type enum for status type."""
    Function = 'Function'

    DAG = 'DAG'

    Loop = 'Loop'

    Unknown = 'Unknown'


class BaseStatus(IOBase):
    """Base Status model"""
    type: constr(regex='^BaseStatus$') = 'BaseStatus'

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


class StepStatus(BaseStatus):
    """The Status of a Simulation Step"""
    type: constr(regex='^StepStatus$') = 'StepStatus'

    id: str = Field(
        ...,
        description='The step unique ID'
    )

    name: str = Field(
        ...,
        description='A human readable name for the step. Usually defined by the '
        'DAG task name but can be extended if the step is part of a loop for example. '
        'This name is unique within the boundary of the DAG/Simulation that generated it.'
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
        'step. In the case of a DAG or a simulation this will be the last step that has '
        'been executed. It will remain empty for functions.'
    )


class SimulationStatus(BaseStatus):
    """Simulation Status."""
    type: constr(regex='^SimulationStatus$') = 'SimulationStatus'

    id: str = Field(
        ...,
        description='The ID of the individual simulation.'
    )

    entrypoint: str = Field(
        None,
        description='The ID of the first step in the simulation.'
    )

    steps: Dict[str, StepStatus] = {}

    outputs: List[StepOutputs] = Field(
        ...,
        description='The outputs produced by this step.'
    )
