"""Queenbee Task Operator class."""
from queenbee.schema.qutil import BaseModel
from pydantic import Field, validator, constr
from typing import List, Any, Set
from enum import Enum


class Operator(BaseModel):
    """Task operator.

    A task operator includes the information for executing tasks from command line
    or in a container.
    """
    type: constr(regex='^operator$') = 'operator'

    name: str = Field(
        ...,
        description='Operator name. This name should be unique among all the operators'
        ' in your workflow.'
    )

    version: str = Field(
        None,
        description='Optional version input for operator.'
    )

    image: str = Field(
        ...,
        description='Docker image name.'
    )
