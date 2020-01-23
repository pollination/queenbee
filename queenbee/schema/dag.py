"""Queenbee DAG steps.

A DAG step defines a single step in the workflow. Each step indicates what task should be
used and maps inputs and outputs for the specific task.
"""
from queenbee.schema.qutil import BaseModel, find_dup_items
from queenbee.schema.arguments import Arguments
from pydantic import Field, root_validator, validator
from typing import List, Any, Union
import queenbee.schema.variable as qbvar


class DAGTask(BaseModel):
    """DAGTask defines a single step in a Directed Acyclic Graph (DAG) workflow."""

    name: str = Field(
        ...,
        description='Name for this step. It must be unique in DAG.'
    )

    arguments: Arguments = Field(
        None,
        description='Input arguments for template.'
    )

    template: str = Field(
        ...,
        description='Template name.'
    )

    dependencies: List[str] = Field(
        None,
        description='Dependencies are name of other DAG steps which this depends on.'
    )

    loop: Union[str, List[Any]] = Field(
        None,
        description='List of inputs to loop over.'
    )

    @validator('loop', each_item=False)
    def check_loop_ref(cls, value):
        if value is None:
            return None
        values = [value] if isinstance(value, str) else value
        for v in values:
            # check for referenced values and validate the format
            ref_var = qbvar.get_ref_variable(v)
            if not ref_var:
                return value
            for rv in ref_var:
                qbvar.validate_ref_variable_format(rv)
        return value

    @root_validator(skip_on_failure=True)
    def check_item_ref(cls, values):
        loop = values.get('loop')
        if not loop:
            return values
        # get referenced values
        name = values.get('name')
        args = values.get('arguments')
        if not args:
            raise ValueError(f'Task "{name}" has a loop value by no arguments.')
        ref_values = args.referenced_values
        # ensure there is a reference to {{item}}
        for rv in ref_values['parameters']:
            for k, v in rv.items():
                for i, j in v.items():
                    for vv in j:
                        if vv.startswith('item'):
                            return values
        for rv in ref_values['artifacts']:
            for k, v in rv.items():
                for i, j in v.items():
                    for vv in j:
                        if vv.startswith('item'):
                            return values
        raise ValueError(
                f'Task "{name}" has a loop but there is no {{item}} reference in'
                ' arguments.'
            )

    @property
    def is_root(self) -> bool:
        """Return true if this function is a root function.

        A root function does not have any dependencies.
        """
        return len(self.dependencies) == 0

    @property
    def referenced_values(self):
        """Get list of referenced values in parameters and artifacts."""
        ref_values = {'arguments': {}, 'loop': []}
        if self.arguments:
            ref_values['arguments'] = self.arguments.referenced_values
        if self.loop:
            values = [self.loop] if isinstance(self.loop, str) else self.loop
            for v in values:
                # check for referenced values and validate the format
                ref_var = qbvar.get_ref_variable(v)
                if ref_var:
                    ref_values['loop'].append({v: ref_var})
        return ref_values


class DAG(BaseModel):
    """DAG includes different steps of a directed acyclic graph."""

    name: str = Field(
        ...,
        description='A unique name for this dag.'
    )

    target: str = Field(
        None,
        description='Target are one or more names of target tasks to execute in a DAG. '
        'Multiple targets can be specified as space delimited inputs. When a target '
        'is provided only a subset of tasks in DAG that are required to generate '
        'the target(s) will be executed.'
    )

    fail_fast: bool = Field(
        True,
        description='Stop scheduling new steps, as soon as it detects that one of the'
        ' DAG nodes is failed. Default is True.'
    )

    tasks: List[DAGTask] = Field(
        ...,
        description='Tasks are a list of DAG steps'
    )

    @root_validator
    def check_task_names(cls, values):
        """Check to ensure there is no duplicate name in tasks.

        This validator also checks for target names to be valid if a target is passed.
        """
        task_names = [t.name for t in values.get('tasks')]
        if len(task_names) != len(set(task_names)):
            dup = find_dup_items(task_names)
            raise ValueError(f'Duplicate parameter names: {dup}')
        targets = values.get('target')
        if not targets:
            return values
        targets = targets.split()
        invalid_targets = [target for target in targets if target not in task_names]
        if invalid_targets:
            raise ValueError(f'Invalid target names: {invalid_targets}')
        return values

    @property
    def artifacts(self):
        """List of unique DAG artifacts."""
        artifacts = []
        for dag_task in self.tasks:
            if not dag_task.arguments:
                continue
            artifacts.append(dag_task.arguments.artifacts)
        return list(artifacts)

    def get_task(self, name):
        """Get task by name."""
        task = [t for t in self.tasks if t.name == name]
        if not task:
            raise ValueError(f'Invalid task name: {name}')
        return task[0]
