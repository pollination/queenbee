"""Queenbee DAG.

A DAG defines a single step in a Recipe. Each DAG is a collection of tasks/steps. Each
step indicates what function template should be used and maps inputs and outputs for the
specific task.
"""
from typing import List, Set, Union, Literal

from pydantic import Field, field_validator, model_validator

from .task import DAGTask
from ..io.common import IOBase, find_dup_items
from ..io.inputs.dag import DAGInputs
from ..io.outputs.dag import DAGOutputs
from ..io.reference import FileReference, FolderReference, TaskReference, \
    TaskFileReference, TaskFolderReference, TaskPathReference
from ..io.outputs.task import TaskPathReturn, TaskReturn


class DAG(IOBase):
    """A Directed Acyclic Graph containing a list of tasks."""
    type: Literal['DAG'] = 'DAG'

    name: str = Field(
        ...,
        description='A unique name for this dag.'
    )

    inputs: List[DAGInputs] = Field(
        default_factory=list,
        description='Inputs for the DAG.'
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

    outputs: List[DAGOutputs] = Field(
        default_factory=list,
        description='Outputs of the DAG that can be used by other DAGs.'
    )

    @staticmethod
    def find_task_return(
        tasks: List[DAGTask],
        reference: Union[
            TaskReference, TaskFileReference, TaskFolderReference, TaskPathReference]
            ) -> Union[TaskReturn, TaskPathReturn]:
        """Find a task output within the DAG from a reference

        Arguments:
            tasks {List[DAGTask]} -- A list of DAG Tasks
            reference {Union[TaskReference, TaskFileReference, TaskFolderReference,
                TaskPathReference]} -- A reference to a DAG Task output

        Raises:
            ValueError: The task name cannot be found.
            ValueError: The task return reference cannot be found.

        Returns:
            Union[TaskReturn, TaskPathReturn] -- A task output parameter or artifact
        """
        filtered_tasks = [x for x in tasks if x.name == reference.name]

        if not filtered_tasks:
            raise ValueError(f'Task with name "{reference.name}" not found.')

        task = filtered_tasks[0]

        if isinstance(reference, TaskReference):
            if task.loop is not None:
                raise ValueError(
                    'Cannot refer to outputs from a looped task.'
                    'You must perform your own aggregation and then refer to '
                    'a hard coded folder path.'
                )

        out = [ret for ret in task.returns if ret.name == reference.variable]
        if not out:
            raise ValueError(
                f'Failed to find referenced variable name "{reference.variable}" in '
                f'"{task.name}" task.'
            )

        return out[0]

    @field_validator('tasks')
    @classmethod
    def check_unique_names(cls, v: List[DAGTask]) -> List[DAGTask]:
        """Check that all tasks have unique names."""
        names = [task.name for task in v]
        duplicates = find_dup_items(names)
        if duplicates:
            raise ValueError(f'Duplicate names: {duplicates}')
        return v

    @field_validator('tasks')
    @classmethod
    def check_dependencies(cls, v: List[DAGTask]) -> List[DAGTask]:
        """Check that all task dependencies exist."""
        task_names = [task.name for task in v]

        exceptions = []
        err_msg = 'DAG Task "{name}" has unresolved dependency: "{dep}"\n'

        for task in v:
            if task.needs is None:
                continue

            for dep in task.needs:
                if dep not in task_names:
                    exceptions.append(err_msg.format(name=task.name, dep=dep))

        if exceptions:
            raise ValueError(''.join(exceptions))

        return v

    @field_validator('tasks', 'inputs', 'outputs')
    @classmethod
    def sort_list(cls, v: list) -> list:
        """Sort the list of tasks, inputs and outputs by name"""
        v.sort(key=lambda x: x.name)
        return v

    @model_validator(mode='after')
    def check_dag_references(self) -> 'DAG':
        """Check references within the DAG."""
        if self.tasks is None:
            # another validation has failed
            return self

        # check_references
        dag_inputs = self.inputs or []
        dag_input_names = set(d.name for d in dag_inputs)
        exceptions = []

        for task in self.tasks:
            if task.arguments is not None:
                # Check DAG input references
                for arg in task.argument_by_ref_source('dag'):
                    if arg.from_.variable not in dag_input_names:
                        exceptions.append(
                            f'Invalid input reference variable: "{arg.from_.variable}" '
                            f'in task "{task.name}"'
                        )

                # Check DAG task inputs
                for arg in task.argument_by_ref_source('task'):
                    try:
                        self.find_task_return(tasks=self.tasks, reference=arg.from_)
                    except ValueError as error:
                        exceptions.append(f'tasks.{task.name}.{arg.name}: {error}')

            # check_template_name
            plugin = task.template.split('/')[0]
            if plugin == self.name:
                raise ValueError('Task cannot refer to its own DAG as a template.')

        if exceptions:
            raise ValueError('\n  '.join(exceptions))

        # check_dag_outputs
        if self.outputs is None:
            return self

        exceptions = []

        for out in self.outputs:
            if isinstance(out.from_, TaskReference):
                try:
                    self.find_task_return(tasks=self.tasks, reference=out.from_)
                except ValueError as error:
                    exceptions.append(f'outputs.{out.name}: {error}')
            elif isinstance(out.from_, (FolderReference, FileReference)):
                # the validation will be checked when the Pydantic model is being loaded
                pass

        if exceptions:
            raise ValueError('\n  '.join(exceptions))

        return self

    def get_task(self, name):
        """Get task by name.

        Arguments:
            name {str} -- The name of a task

        Raises:
            ValueError: The task name does not exist

        Returns:
            DAGTask -- A DAG Task
        """
        task = [t for t in self.tasks if t.name == name]
        if not task:
            raise ValueError(f'Invalid task name: {name}')
        return task[0]

    @property
    def templates(self) -> Set[str]:
        """A list of unique templates referred to in the DAG.

        Returns:
            List[str] -- A list of task name
        """
        return set([task.template for task in self.tasks])
