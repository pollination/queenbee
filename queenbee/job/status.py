"""Queenbee status base class.

The base status class provides reusable primitives to
express the status of a job, run or step
"""
from datetime import datetime
from pydantic import Field, constr
from ..io.common import IOBase

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

    source: str = Field(
        None,
        description='Source url for the status object. It can be a recipe or a function.'
    )

