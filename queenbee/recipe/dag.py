"""Queenbee DAG steps.

A DAG step defines a single step in the workflow. Each step indicates what task should be
used and maps inputs and outputs for the specific task.
"""
from enum import Enum
from typing import List, Any, Union, Dict
from pydantic import Field, validator, ValidationError

from ..base.basemodel import BaseModel
from ..base.io import IOBase, find_dup_items
from ..operator.function import Function
from .artifact_source import HTTPSource, S3Source, ProjectFolderSource
from .reference import InputArtifactReference, InputParameterReference, \
    TaskArtifactReference, TaskParameterReference, ItemParameterReference

class DAGInputParameter(BaseModel):
    """Parameter.

    Parameter indicate a passed string parameter to a service template with an optional
    default value.
    """

    name: str = Field(
        ...,
        description='Name is the parameter name. must be unique within a task\'s '
        'inputs.'
    )

    default: str = Field(
        None,
        description='Default value to use for an input parameter if a value was not'
        ' supplied.'
    )

    description: str = Field(
        None,
        description='Optional description for input parameter.'
    )

    required: bool = Field(
        None,
        description='Whether this value must be specified in a task argument.'
    )

    @validator('required')
    def validate_required(cls, v, values):
        """Ensure parameter with no default value is marked as required"""
        default = values.get('default')

        if default is None and v is False:
            raise ValueError(
                'required should be true if no default is provided'
            )
        elif default is None:
            v = True

        return v


    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        """Get referenced variables if any"""
        return self._referenced_values(['default'])




class DAGInputArtifact(BaseModel):

    name: str = Field(
        ...,
        description='The name of the artifact within the scope of the DAG'
    )

    description: str = Field(
        None,
        description='Optional description for the input artifact'
    )

    default: Union[HTTPSource, S3Source, ProjectFolderSource] = Field(
        None,
        description='If no artifact is specified then pull it from this source location.'
    )
    
    required: bool = Field(
        None,
        description='Whether this value must be specified in a task argument.'
    )

    @validator('required')
    def validate_required(cls, v, values):
        """Ensure parameter with no default value is marked as required"""
        default = values.get('default')

        if default is None and v is False:
            raise ValueError(
                'required should be true if no default is provided'
            )
        elif default is None:
            v = True

        return v



class DAGInputs(IOBase):

    parameters: List[DAGInputParameter] = Field(
        [],
        description='A list of parameters the DAG will use as input values'
    )

    artifacts: List[DAGInputArtifact] = Field(
        [],
        description='A list of artifacts the DAG will use'
    )


class DAGOutputParameter(BaseModel):

    name: str = Field(
        ...,
        description='The name of the output variable'
    )

    from_: TaskParameterReference = Field(
        ...,
        alias='from',
        description='The task reference to pull this output variable from. Note, this must be an output variable.'
    )

class DAGOutputArtifact(BaseModel):

    name: str = Field(
        ...,
        description='The name of the output variable'
    )

    from_: TaskArtifactReference = Field(
        ...,
        alias='from',
        description='The task reference to pull this output variable from. Note, this must be an output variable.'
    )

class DAGOutputs(IOBase):

    parameters: List[DAGOutputParameter] = Field(
        [],
        description='A list of output parameters exposed by this DAG'
    )

    artifacts: List[DAGOutputArtifact] = Field(
        [],
        description='A list of output artifacts exposed by this DAG'
    )

class DAGTaskArtifactArgument(BaseModel):

    name: str = Field(
        ...,
        description='Name of the argument variable'
    )

    from_: Union[InputArtifactReference, TaskArtifactReference] = Field(
        ...,
        alias='from',
        description='The previous task or global workflow variable to pull this argument from'
    )

    subpath: str = Field(
        None,
        description='Specify this value if your source artifact is a repository and you want to '
        'source an artifact from within that directory.'
    )


class DAGTaskParameterArgument(BaseModel):

    name: str = Field(
        ...,
        description='Name of the argument variable'
    )

    from_: Union[InputParameterReference, TaskParameterReference, ItemParameterReference] = Field(
        None,
        alias='from',
        description='The previous task or global workflow variable to pull this argument from'
    )

    value: str = Field(
        None,
        description='The fixed value for this task argument'
    )

    @validator('value')
    def check_value_exists(cls, v):
        if v is not None:
            assert v.from_ is not None, \
                ValueError('value must be specified if no "from" source is specified for argument parameter')
        return v

class DAGTaskArgument(IOBase):

    artifacts: List[DAGTaskArtifactArgument] = Field(
        [],
        description='A list of input artifacts to pass to the task'
    )

    parameters: List[DAGTaskParameterArgument] = Field(
        [],
        description='A list of input parameters to pass to the task'
    )


    def artifacts_by_ref_source(self, source) -> List[DAGTaskArtifactArgument]:
        if self.artifacts is None:
            return []

        source_class = None
        
        if source == 'dag':
            source_class = InputArtifactReference
        elif source == 'task':
            source_class = TaskArtifactReference
        else:
            raise ValueError('reference source string should be one of ["dag", "task"], not {source}')

        return  [x for x in self.artifacts if isinstance(x.from_, source_class)]

    def parameters_by_ref_source(self, source) -> List[DAGTaskParameterArgument]:
        if self.parameters is None:
            return []
        
        source_class = None
        
        if source == 'dag':
            source_class = InputParameterReference
        elif source == 'task':
            source_class = TaskParameterReference
        elif source == 'item':
            source_class = ItemParameterReference
        else:
            raise ValueError('reference source string should be one of ["dag", "task", "item"], not {source}')

        return  [x for x in self.parameters if isinstance(x.from_, source_class)]

class DAGTaskOutputArtifact(BaseModel):

    name: str = Field(
        ...,
        description='The name of the output variable'
    )

    path: str = Field(
        ...,
        description='The path where the artifact should be saved relative to the DAG folder.'
    )


class DAGTaskOutputParameter(BaseModel):

    name: str = Field(
        ...,
        description='The name of the output variable'
    )


class DAGTaskOutputs(IOBase):

    artifacts: List[DAGTaskOutputArtifact] = Field(
        [],
        description='A list of output artifacts to expose from the task'
    )

    parameters: List[DAGTaskOutputParameter] = Field(
        [],
        description='A list of output parameters to expose from the task'
    )

class DAGTaskLoop(BaseModel):


    from_: Union[InputParameterReference, TaskParameterReference] = Field(
        None,
        alias='from',
        description='The task or DAG parameter to loop over (must be a list of some sort).'
    )

    value: List[Union[str, int, float, dict]] = Field(
        None,
        description='A list of values or JSON objects to loop over.'
    )

    sub_folders: List[str] = Field(
        ['item'],
        description='An ordered list of the name of the item keys to loop over. Only applies if the item is a JSON object.',
        example=[
            'item.country',
            'item.region',
            'item.city'
        ]
    )


class DAGTask(BaseModel):
    """DAGTask defines a single step in a Directed Acyclic Graph (DAG) workflow."""

    name: str = Field(
        ...,
        description='Name for this step. It must be unique in DAG.'
    )

    template: str = Field(
        ...,
        description='Template name.'
    )

    arguments: DAGTaskArgument = Field(
        None,
        description='The input arguments for this task'
    )

    dependencies: List[str] = Field(
        None,
        description='Dependencies are name of other DAG steps which this depends on.'
    )

    loop: DAGTaskLoop = Field(
        None,
        description='List of inputs to loop over.'
    )

    outputs: DAGTaskOutputs = Field(
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
                ValueError('Cannot use "item" references in argument parameters if no "loop" is specified')
        return v

    @property
    def is_root(self) -> bool:
        """Return true if this function is a root function.

        A root function does not have any dependencies.
        """
        return len(self.dependencies) == 0

    
    def check_template(self, template: IOBase):
        """A function to check the inputs and outputs of a DAG task match a certain template

        Arguments:
            template {Union[DAG, Function]} -- A DAG or Function template
        """
        if template.inputs is not None:
            for param in template.inputs.parameters:
                if param.required:
                    try:
                        self.arguments.parameter_by_name(param.name)
                    except ValueError as error:
                        raise ValueError(
                                f'Validation Error for Task {self.name} and Template {template.name}: \n'
                                f'\t{str(error)}'
                            )

            for art in template.inputs.artifacts:
                # if art.required:
                try:
                    self.arguments.artifact_by_name(art.name)
                except ValueError as error:
                    raise ValueError(
                            f'Validation Error for Task {self.name} and Template {template.name}: \n'
                            f'\t{str(error)}'
                        )

        if self.outputs is not None:
            for param in self.outputs.parameters:
                try:
                    template.outputs.parameter_by_name(param.name)
                except ValueError as error:
                    raise ValueError(
                            f'Validation Error for Task {self.name} and Template {template.name}: \n'
                            f'{str(error)}'
                        )

            for art in self.outputs.artifacts:
                try:
                    template.outputs.artifact_by_name(art.name)
                except ValueError as error:
                    raise ValueError(
                            f'Validation Error for Task {self.name} and Template {template.name}: \n'
                            f'{str(error)}'
                        )



class DAG(BaseModel):
    """DAG includes different steps of a directed acyclic graph."""

    name: str = Field(
        ...,
        description='A unique name for this dag.'
    )

    inputs: DAGInputs = Field(
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

    outputs: DAGOutputs = Field(
        None,
        description='Outputs of the DAG that can be used by other DAGs'
    )


    @staticmethod
    def find_task_output(
        tasks: List[DAGTask],
        reference: Union[TaskArtifactReference, TaskParameterReference]
    ):
        filtered_tasks = [x for x in tasks if x.name == reference.name]

        if len(filtered_tasks) != 1:
            raise ValueError(
                f'Task with name "{reference.name}" not found'
            )

        task = filtered_tasks[0]

        if isinstance(reference, TaskArtifactReference):
            return task.outputs.artifact_by_name(reference.variable)
        elif isinstance(reference, TaskParameterReference):
            return task.outputs.parameter_by_name(reference.variable)
        else:
            raise ValueError(f'Unexpected output_type "{type(reference)}". Wanted one of "TaskArtifactReference" or "TaskParameterReference".')


    @validator('tasks')
    def check_unique_names(cls, v):
        names = [task.name for task in v]
        duplicates = find_dup_items(names)
        if len(duplicates) != 0:
            raise ValueError(f'Duplicate names: {duplicates}')
        return v

    @validator('tasks')
    def check_dependencies(cls, v):
        task_names = [task.name for task in v]

        exceptions = []

        for task in v:
            if task.dependencies is None:
                continue

            if not all(dep in task_names  for dep in task.dependencies):
                exceptions.append(
                    ValueError(f'DAG Task "{task.name}" has unresolved dependencies: {task.dependencies}')
                    )

        if exceptions != []:
            raise ValueError(exceptions)
        
        return v


    @validator('tasks')
    def check_inputs(cls, v, values):
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



    @validator('tasks')
    def sort_list(cls, v):
        v.sort(key=lambda x: x.name)
        return v
        
    @validator('outputs')
    def check_task_outputs(cls, v, values):

        tasks = values.get('tasks')
        exceptions = []

        for artifact in v.artifacts:
            try:
                cls.find_task_output(
                    tasks=tasks,
                    reference=artifact.from_,
                    )
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
        """Get task by name."""
        task = [t for t in self.tasks if t.name == name]
        if not task:
            raise ValueError(f'Invalid task name: {name}')
        return task[0]
