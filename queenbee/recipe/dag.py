"""Queenbee DAG steps.

A DAG step defines a single step in a Recipe. Each step indicates what function template
should be used and maps inputs and outputs for the specific task.
"""
from typing import List, Union, Dict
from pydantic import Field, validator

from ..base.basemodel import BaseModel
from ..base.io import IOBase, find_dup_items
from ..base.parser import parse_double_quotes_vars
from .artifact_source import HTTPSource, S3Source, ProjectFolderSource
from .reference import InputArtifactReference, InputParameterReference, \
    TaskArtifactReference, TaskParameterReference, ItemParameterReference


class DAGInputParameter(BaseModel):
    """An input parameter used within the DAG."""

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
        """Get all referenced values specified by var name

        Returns:
            Dict[str, List[str]] -- A dictionary where each key corresponds to a class
                attribute indexing a list of referenced values
        """
        return self._referenced_values(['default'])


class DAGInputArtifact(BaseModel):
    """An artifact used within the DAG."""

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
    """Inputs of a DAG."""

    parameters: List[DAGInputParameter] = Field(
        [],
        description='A list of parameters the DAG will use as input values'
    )

    artifacts: List[DAGInputArtifact] = Field(
        [],
        description='A list of artifacts the DAG will use'
    )


class DAGOutputParameter(BaseModel):
    """A parameter sourced from within the DAG that is exposed as an output."""

    name: str = Field(
        ...,
        description='The name of the output variable'
    )

    from_: TaskParameterReference = Field(
        ...,
        alias='from',
        description='The task reference to pull this output variable from. Note, this '
        'must be an output variable.'
    )


class DAGOutputArtifact(BaseModel):
    """An artifact sourced from within the DAG that is exposed as an output"""

    name: str = Field(
        ...,
        description='The name of the output variable'
    )

    from_: TaskArtifactReference = Field(
        ...,
        alias='from',
        description='The task reference to pull this output variable from. Note, this'
        ' must be an output variable.'
    )


class DAGOutputs(IOBase):
    """Artifacts and Parameters exposed by the DAG"""

    parameters: List[DAGOutputParameter] = Field(
        [],
        description='A list of output parameters exposed by this DAG'
    )

    artifacts: List[DAGOutputArtifact] = Field(
        [],
        description='A list of output artifacts exposed by this DAG'
    )


class DAGTaskArtifactArgument(BaseModel):
    """Input argument for a DAG task.

    The name must correspond to an input artifact from the template function the task
    refers to.
    """

    name: str = Field(
        ...,
        description='Name of the argument variable'
    )

    from_: Union[InputArtifactReference, TaskArtifactReference] = Field(
        ...,
        alias='from',
        description='The previous task or global workflow variable to pull this argument'
        ' from'
    )

    subpath: str = Field(
        None,
        description='Specify this value if your source artifact is a repository and you'
        ' want to source an artifact from within that directory.'
    )


class DAGTaskParameterArgument(BaseModel):
    """Input argument for a DAG task.

    The name must correspond to an input parameter from the template function the task
    refers to.
    """

    name: str = Field(
        ...,
        description='Name of the argument variable'
    )

    from_: Union[
            InputParameterReference, TaskParameterReference, ItemParameterReference
        ] = Field(
            None,
            alias='from',
            description='The previous task or global workflow variable to pull this'
            ' argument from'
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
    """DAG task argument.

    These arguments should match the inputs from the template referenced in the task.
    """

    artifacts: List[DAGTaskArtifactArgument] = Field(
        [],
        description='A list of input artifacts to pass to the task'
    )

    parameters: List[DAGTaskParameterArgument] = Field(
        [],
        description='A list of input parameters to pass to the task'
    )

    def artifacts_by_ref_source(self, source) -> List[DAGTaskArtifactArgument]:
        """Retrieve a list of argument artifacts by their source type.

        Arguments:
            source {str} -- The source type, one of: 'dag', 'task'

        Raises:
            ValueError: The source type is not recognized

        Returns:
            List[DAGTaskArtifactArgument] -- A list of Argument Artifacts
        """
        if self.artifacts is None:
            return []

        source_class = None

        if source == 'dag':
            source_class = InputArtifactReference
        elif source == 'task':
            source_class = TaskArtifactReference
        else:
            raise ValueError(
                'reference source string should be one of ["dag", "task"], not {source}'
            )

        return [x for x in self.artifacts if isinstance(x.from_, source_class)]

    def parameters_by_ref_source(self, source) -> List[DAGTaskParameterArgument]:
        """Retrieve an list of argument parameters by their source type.

        Arguments:
            source {str} -- The source type, one of: 'dag', 'task', 'item'

        Raises:
            ValueError: The source type is not recognized

        Returns:
            List[DAGTaskParameterArgument] -- A list of Argument Parameters
        """
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
            raise ValueError(
                'reference source string should be one of ["dag", "task", "item"], '
                'not {source}'
            )

        return [x for x in self.parameters if isinstance(x.from_, source_class)]


class DAGTaskOutputArtifact(BaseModel):
    """Output artifact for a DAG task.

    The name must correspond to an output artifact from the template function the task
    refers to.
    """

    name: str = Field(
        ...,
        description='The name of the output variable'
    )

    path: str = Field(
        None,
        description='The path where the artifact should be saved relative to the DAG'
        ' folder.'
    )


class DAGTaskOutputParameter(BaseModel):
    """Output parameter for a DAG task.

    The name must correspond to an output parameter from the template function the task
    refers to.
    """

    name: str = Field(
        ...,
        description='The name of the output variable'
    )


class DAGTaskOutputs(IOBase):
    """These outputs should match the outputs from the template referenced in the task"""

    artifacts: List[DAGTaskOutputArtifact] = Field(
        [],
        description='A list of output artifacts to expose from the task'
    )

    parameters: List[DAGTaskOutputParameter] = Field(
        [],
        description='A list of output parameters to expose from the task'
    )


class LoopControl(BaseModel):
    """Loop Control"""

    key: str = Field(
        None,
        description='The loop control key determines how parameters and artifacts from a looped task can be identified'
    )

    @validator('key')
    def check_template(cls, v):

        if v is None:
            return

        refs = parse_double_quotes_vars(v)

        if len(refs) == 0:
            raise ValueError(f'Loop Control Key must have templated values from the `item` variable. eg: `{{{{item.foo}}}}-{{{{item.bar}}}}')

        for ref in refs:
            is_item = ref == 'item'
            is_item_key = ref.startswith('item.')

            if not is_item and not is_item_key:
                raise ValueError(f'Loop control template must be `{{{{item}}}}` or `{{{{item.<var-name>}}}}`. Not: `{{{{{ref}}}}}`')

        return v


class DAGTaskLoop(BaseModel):
    """Loop configuration for the task.

    This will run the template provided multiple times and in parallel relative to an
    input or task parameter which should be a list.
    """

    from_: Union[InputParameterReference, TaskParameterReference] = Field(
        None,
        alias='from',
        description='The task or DAG parameter to loop over (must be iterable).'
    )

    value: List[Union[str, int, float, dict]] = Field(
        None,
        description='A list of values or JSON objects to loop over.'
    )

    control: LoopControl = Field(
        None,
        description='Parameters to control some loop behavior for this task'
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

    sub_folder: str = Field(
        None,
        description='A path relative to the current folder context where artifacts should '
        'be saved. This is useful when performing a loop or invoking another workflow and '
        'wanting to save results in a specific folder.'
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
                ValueError(
                    'Cannot use "item" references in argument parameters if no'
                    ' "loop" is specified'
                )
        return v

    @validator('sub_folder')
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
                assert ref.startswith('arguments.parameters.'), f'Sub folder ref must be from `item` or `arguments.parameters`. Not: {ref}'
                assert len(ref_list) == 3, f'Sub folder ref must follow format `arguments.parameters.<var-name>`. Not {ref}'
                # Check parameter is set
                arguments.parameter_by_name(ref_list[2])

        return v


    @validator('arguments', always=True)
    def set_default_args(cls, v):
         return DAGTaskArgument() if v is None else v

    @validator('outputs', always=True)
    def set_default_outputs(cls, v):
         return DAGTaskOutputs() if v is None else v

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
                    print('WARNING: Setting a persistence path for a DAG template will have no effect.')

                if art.path is None and isinstance(template, TemplateFunction):
                    print('WARNING: Not setting a persistence path for a Function template '
                    'means the artifact will be saved in an arbitrary folder.')


class DAG(BaseModel):
    """A Directed Acyclic Graph containing a list of tasks."""

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
    ) -> Union[DAGTaskOutputArtifact, DAGTaskOutputParameter]:
        """Find a task output within the DAG from a reference

        Arguments:
            tasks {List[DAGTask]} -- A list of DAG Tasks
            reference {Union[TaskArtifactReference, TaskParameterReference]} -- A
                reference to a DAG Task output

        Raises:
            ValueError: The task output reference cannot be found

        Returns:
            Union[DAGTaskOutputArtifact, DAGTaskOutputParameter] -- A task output
                parameter or artifact
        """
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
            raise ValueError(
                f'Unexpected output_type "{type(reference)}".'
                f' Expected one of "TaskArtifactReference" or "TaskParameterReference".'
            )

    @validator('inputs', always=True)
    def set_default_inputs(cls, v):
         return DAGInputs() if v is None else v

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
