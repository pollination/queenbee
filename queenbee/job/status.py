"""Queenbee status base class.

The base status class provides reusable primitives to
express the status of a job, run or step
"""
from datetime import datetime
from pydantic import Field
from ..io.common import IOBase
from typing import Literal, Union

class BaseStatus(IOBase):
    """Base Status model"""
    type: Literal['BaseStatus'] = 'BaseStatus'

    message: Union[str, None] = Field(
        None,
        description='Any message produced by the task. Usually error/debugging hints.'
    )

    started_at: datetime = Field(
        ...,
        description='The time at which the task was started'
    )

    finished_at: Union[datetime, None] = Field(
        None,
        description='The time at which the task was completed'
    )

    source: Union[str, None] = Field(
        None,
        description='Source url for the status object. It can be a recipe or a function.'
    )
