"""Argument and Return objects for tasks.

Task argument and return objects provide the interface to connect:

 * DAG inputs to function inputs
 * DAG inputs to DAG inputs  -- for nested DAGs
 * function outputs to following function inputs
 * function outputs to DAG outputs
 * DAG outputs to DAG outputs  -- for nested DAGs

"""

from typing import Union
from pydantic import constr
from ..common import GenericOutput, PathOutput


# Task returns
class TaskReturn(GenericOutput):
    """A Task return output that exposes the values from a function or a DAG."""

    type: constr(regex='^TaskReturn$') = 'TaskReturn'

    @property
    def is_artifact(self):
        return False


class TaskPathReturn(PathOutput):
    """A Task output that returns a file or a folder output from a function or a DAG."""

    type: constr(regex='^TaskPathReturn$') = 'TaskPathReturn'

    @property
    def is_artifact(self):
        return True


TaskReturns = Union[TaskReturn, TaskPathReturn]
