"""Queenbee DAG steps.

A DAG step defines a single step in a Recipe. Each step indicates what function template
should be used and maps inputs and outputs for the specific task.
"""
from typing import List, Union
from pydantic import Field, validator

from ..base.basemodel import BaseModel
from ..io import IOBase, find_dup_items
from ..base.parser import parse_double_quotes_vars
from ..io.dag import DAGInputs, DAGOutputs
from ..io.reference import InputReference, TaskReference, ValueListReference, \
    references_from_string
from ..io.task import TaskArguments, TaskReturns


class DAGTaskLoop(BaseModel):
    """Loop configuration for the task.

    This will run the template provided multiple times and in parallel relative to an
    input or task parameter which should be a list.
    """

    from_: Union[InputReference, TaskReference, ValueListReference] = Field(
        None,
        alias='from',
        description='The task or DAG parameter to loop over (must be iterable).'
    )


class DAGTask(BaseModel):
    """The instance of a function template matched with DAG inputs and outputs."""

    name: str = Field(
        ...,
        description='Name for this step. It must be unique in DAG.'
    )

    template: str = Field(
        ...,
        description='Template name.'
    )

    arguments: TaskArguments = Field(
        None,
        description='The input arguments for this task.'
    )

    dependencies: List[str] = Field(
        None,
        description='Dependencies are name of other DAG steps which this depends on.'
    )

    loop: DAGTaskLoop = Field(
        None,
        description='List of inputs to loop over.'
    )

    sub_folder: str = Field(
        None,
        description='A path relative to the current folder context where artifacts should '
        'be saved. This is useful when performing a loop or invoking another workflow and '
        'wanting to save results in a specific folder.'
    )

    returns: TaskReturns = Field(
        None,
        description='The outputs of this task'
    )

    @validator('loop', always=True)
    def check_item_references(cls, v, values):
        if v is None:
            arguments = values.get('arguments')
            if arguments is None:
                return v
            assert len(arguments.parameters_by_ref_source('item')) == 0, \
                ValueError(
                    'Cannot use "item" references in argument parameters if no'
                    ' "loop" is specified'
            )
        return v

    @validator('sub_folder', always=True)
    def check_references(cls, v, values):
        loop = values.get('loop')
        arguments = values.get('arguments')

        if v is None:
            return v

        refs = parse_double_quotes_vars(v)

        for ref in refs:
            if ref == 'item' or ref.startswith('item.'):
                assert loop is not None, 'Cannot use `item` if no loop is specified'
            else:
                ref_list = ref.split('.')
                assert ref.startswith(
                    'arguments.parameters.'), f'Sub folder ref must be from `item` or `arguments.parameters`. Not: {ref}'
                assert len(
                    ref_list) == 3, f'Sub folder ref must follow format `arguments.parameters.<var-name>`. Not {ref}'
                # Check parameter is set
                arguments.parameter_by_name(ref_list[2])

        return v

    @validator('arguments', always=True)
    def set_default_args(cls, v):
        return [] if v is None else v

    @validator('returns', always=True)
    def set_default_outputs(cls, v):
        return [] if v is None else v

    @property
    def is_root(self) -> bool:
        """A root task does not have any dependencies

        Returns:
            bool -- True if the task has no dependencies
        """
        if self.dependencies:
            return len(self.dependencies) == 0
        else:
            return True

    def check_template(self, template: IOBase):
        """A function to check the inputs and outputs of a DAG task.

        The DAG tasks should match a certain template.

        Arguments:
            template {Union[DAG, Function]} -- A DAG or Function template

        Raises:
            ValueError: The task input and output values do not match the task template
        """
        from .dag import DAG
        from .recipe import TemplateFunction

        if template.inputs is not None:
            for param in template.inputs.parameters:
                if param.required:

                    if self.arguments is None:
                        raise ValueError(
                            f'Validation Error for Task {self.name} and '
                            f'Template {template.name}: \n\tMissing task arguments'
                        )

                    try:
                        self.arguments.parameter_by_name(param.name)
                    except ValueError as error:
                        raise ValueError(
                            f'Validation Error for Task {self.name} and '
                            f'Template {template.name}: \n\t{str(error)}'
                        )

            for art in template.inputs.artifacts:

                if self.arguments is None:
                    raise ValueError(
                        f'Validation Error for Task {self.name} and '
                        f'Template {template.name}: \n\tMissing task arguments'
                    )

                try:
                    self.arguments.artifact_by_name(art.name)
                except ValueError as error:
                    raise ValueError(
                        f'Validation Error for Task {self.name} and '
                        f'Template {template.name}: \n\t{str(error)}'
                    )

        if self.outputs is not None:
            if template.outputs is None:
                raise ValueError(
                    f'Validation Error for Task {self.name} and '
                    f'Template {template.name}: \n'
                    f'\tTask expects outputs but template does not have any'
                )
            for param in self.outputs.parameters:
                try:
                    template.outputs.parameter_by_name(param.name)
                except ValueError as error:
                    raise ValueError(
                        f'Validation Error for Task {self.name} and'
                        f' Template {template.name}: \n{str(error)}'
                    )

            for art in self.outputs.artifacts:
                try:
                    template.outputs.artifact_by_name(art.name)
                except ValueError as error:
                    raise ValueError(
                        f'Validation Error for Task {self.name} and'
                        f' Template {template.name}: \n{str(error)}'
                    )

                if art.path is not None and isinstance(template, DAG):
                    print(
                        'WARNING: Setting a persistence path for a DAG template will have no effect.')

                if art.path is None and isinstance(template, TemplateFunction):
                    print('WARNING: Not setting a persistence path for a Function template '
                          'means the artifact will be saved in an arbitrary folder.')


# TODO: Add these methods to the DAGTask itself.
# class DAGTaskArgument(IOBase):

#     def artifacts_by_ref_source(self, source) -> List[DAGTaskArtifactArgument]:
#         """Retrieve a list of argument artifacts by their source type.

#         Arguments:
#             source {str} -- The source type, one of: 'dag', 'task'

#         Raises:
#             ValueError: The source type is not recognized

#         Returns:
#             List[DAGTaskArtifactArgument] -- A list of Argument Artifacts
#         """
#         if self.artifacts is None:
#             return []

#         source_class = None

#         if source == 'dag':
#             source_class = InputArtifactReference
#         elif source == 'task':
#             source_class = TaskReference
#         else:
#             raise ValueError(
#                 'reference source string should be one of ["dag", "task"], not {source}'
#             )

#         return [x for x in self.artifacts if isinstance(x.from_, source_class)]

#     def parameters_by_ref_source(self, source) -> List[DAGTaskParameterArgument]:
#         """Retrieve an list of argument parameters by their source type.

#         Arguments:
#             source {str} -- The source type, one of: 'dag', 'task', 'item'

#         Raises:
#             ValueError: The source type is not recognized

#         Returns:
#             List[DAGTaskParameterArgument] -- A list of Argument Parameters
#         """
#         if self.parameters is None:
#             return []

#         source_class = None

#         if source == 'dag':
#             source_class = InputParameterReference
#         elif source == 'task':
#             source_class = TaskParameterReference
#         elif source == 'item':
#             source_class = ItemParameterReference
#         else:
#             raise ValueError(
#                 'reference source string should be one of ["dag", "task", "item"], '
#                 'not {source}'
#             )

#         return [x for x in self.parameters if isinstance(x.from_, source_class)]


class DAG(BaseModel):
    """A Directed Acyclic Graph containing a list of tasks."""

    name: str = Field(
        ...,
        description='A unique name for this dag.'
    )

    inputs: List[DAGInputs] = Field(
        None,
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
        None,
        description='Outputs of the DAG that can be used by other DAGs'
    )

    # @staticmethod
    # def find_task_output(
    #     tasks: List[DAGTask],
    #     reference: Union[TaskReference, TaskPathReference]
    #         ) -> Union[DAGTaskOutputArtifact, DAGTaskOutputParameter]:
    #     """Find a task output within the DAG from a reference

    #     Arguments:
    #         tasks {List[DAGTask]} -- A list of DAG Tasks
    #         reference {Union[TaskReference, TaskParameterReference]} -- A
    #             reference to a DAG Task output

    #     Raises:
    #         ValueError: The task output reference cannot be found

    #     Returns:
    #         Union[DAGTaskOutputArtifact, DAGTaskOutputParameter] -- A task output
    #             parameter or artifact
    #     """
    #     filtered_tasks = [x for x in tasks if x.name == reference.name]

    #     if len(filtered_tasks) != 1:
    #         raise ValueError(
    #             f'Task with name "{reference.name}" not found'
    #         )

    #     task = filtered_tasks[0]

    #     if isinstance(reference, TaskReference):
    #         if task.loop is not None:
    #             raise ValueError(
    #                 'Cannot refer to outputs from a looped task.'
    #                 'You must perform your own aggregation and then refer to '
    #                 'a hard coded folder path.'
    #             )
    #         return task.outputs.artifact_by_name(reference.variable)
    #     elif isinstance(reference, TaskParameterReference):
    #         return task.outputs.parameter_by_name(reference.variable)
    #     else:
    #         raise ValueError(
    #             f'Unexpected output_type "{type(reference)}".'
    #             f' Expected one of "TaskReference" or "TaskParameterReference".'
    #         )

    @validator('inputs', always=True)
    def set_default_inputs(cls, v):
        return [] if v is None else v

    @validator('outputs', always=True)
    def set_default_outputs(cls, v):
        return DAGOutputs() if v is None else v

    @validator('tasks')
    def check_unique_names(cls, v):
        """Check that all tasks have unique names."""
        names = [task.name for task in v]
        duplicates = find_dup_items(names)
        if len(duplicates) != 0:
            raise ValueError(f'Duplicate names: {duplicates}')
        return v

    @validator('tasks')
    def check_dependencies(cls, v):
        """Check that all task dependencies exist."""
        task_names = [task.name for task in v]

        exceptions = []

        for task in v:
            if task.dependencies is None:
                continue

            if not all(dep in task_names for dep in task.dependencies):
                exceptions.append(
                    ValueError(
                        f'DAG Task "{task.name}" has unresolved dependencies:'
                        f' {task.dependencies}'
                    )
                )

        if exceptions != []:
            raise ValueError(exceptions)

        return v

    @validator('tasks')
    def check_references(cls, v, values):
        """Check that input and output references exist."""
        dag_inputs = values.get('inputs', DAGInputs())

        exceptions = []

        for task in v:
            if task.arguments is None:
                continue

            # Check all DAG input refs exist
            for artifact in task.arguments.artifacts_by_ref_source('dag'):
                try:
                    dag_inputs.artifact_by_name(artifact.from_.variable)
                except ValueError as error:
                    exceptions.append(error)

            for parameter in task.arguments.parameters_by_ref_source('dag'):
                try:
                    dag_inputs.parameter_by_name(parameter.from_.variable)
                except ValueError as error:
                    exceptions.append(error)

            # Check all task output refs exist
            for artifact in task.arguments.artifacts_by_ref_source('task'):
                try:
                    cls.find_task_output(
                        tasks=v,
                        reference=artifact.from_,
                    )
                except ValueError as error:
                    exceptions.append(error)

            for parameter in task.arguments.parameters_by_ref_source('task'):
                try:
                    cls.find_task_output(
                        tasks=v,
                        reference=parameter.from_,
                    )
                except ValueError as error:
                    exceptions.append(error)

        if exceptions != []:
            raise ValueError(exceptions)

        return v

    @validator('tasks', each_item=True)
    def check_template_name(cls, v, values):
        """Check that a task name does not refer to itself in a template."""
        name = values.get('name')

        operator = v.template.split('/')[0]

        assert operator != name, \
            ValueError(f'Task cannot refer to its own DAG as a template')

        return v

    @validator('tasks')
    def sort_list(cls, v):
        """Sort the list of tasks by name"""
        v.sort(key=lambda x: x.name)
        return v

    @validator('outputs')
    def check_dag_outputs(cls, v, values):
        """Check DAG outputs refer to existing Task outputs"""
        if v is None:
            return v

        tasks = values.get('tasks')
        inputs = values.get('inputs')
        exceptions = []

        for artifact in v.artifacts:
            try:
                if artifact.from_.type.value == 'tasks':
                    cls.find_task_output(
                        tasks=tasks,
                        reference=artifact.from_,
                    )
                elif artifact.from_.type.value == 'folder':
                    refs = references_from_string(artifact.from_.path)
                    for ref in refs:
                        if ref.type == 'tasks':
                            cls.find_task_output(
                                tasks=tasks,
                                reference=ref
                            )
                        if ref.type == 'inputs':
                            inputs.parameter_by_name(ref.variable)
                        else:
                            raise ValueError(
                                'Reference of type {ref.type.value} is not supported for DAG folder output path')
                else:
                    raise ValueError(
                        f'DAG output of type {artifact.from_.type.value} is not supported')
            except ValueError as error:
                exceptions.append(error)

        for parameter in v.parameters:
            try:
                cls.find_task_output(
                    tasks=tasks,
                    reference=parameter.from_,
                )
            except ValueError as error:
                exceptions.append(error)

        if exceptions != []:
            raise ValueError(exceptions)

        return v

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
    def templates(self) -> List[str]:
        """A list of unique templates referred to in the DAG.

        Returns:
            List[str] -- A list of task name
        """
        return set([task.template for task in self.tasks])
