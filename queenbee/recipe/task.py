"""DAGTask module."""
from typing import Union, List
from pydantic import Field, validator

from ..base.basemodel import BaseModel
from ..io.common import find_io_by_name
from ..io.reference import InputReference, TaskReference, ValueListReference, \
    InputFileReference, InputFolderReference, InputPathReference, \
    TaskFileReference, TaskFolderReference, TaskPathReference, \
    ValueFileReference, ValueFolderReference, ItemReference, ValueReference
from ..io.task import TaskArguments, TaskReturns
from ..base.parser import parse_double_quotes_vars


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
    """A single task in a DAG flow."""

    name: str = Field(
        ...,
        description='Name for this task. It must be unique in a DAG.'
    )

    template: str = Field(
        ...,
        description='Template name. A template is a Function or a DAG. This template '
        'must be available in the dependencies.'
    )

    arguments: List[TaskArguments] = Field(
        None,
        description='The input arguments for this task.'
    )

    needs: List[str] = Field(
        None,
        description='List of DAG tasks that this task depends on and needs to be'
        ' executed before this task.'
    )

    loop: DAGTaskLoop = Field(
        None,
        description='Loop configuration for this task.'
    )

    sub_folder: str = Field(
        None,
        description='A path relative to the current folder context where artifacts '
        'should be saved. This is useful when performing a loop or invoking another '
        'workflow and wanting to save results in a specific sub_folder.'
    )

    returns: List[TaskReturns] = Field(
        None,
        description='List of task returns.'
    )

    @validator('loop', always=True)
    def check_item_references(cls, v, values):
        if v is None:
            arguments = values.get('arguments')
            if arguments is None:
                return v
            artifacts = [arg for arg in arguments if arg.is_artifact]
            assert len(cls.parameters_by_ref_source(artifacts, 'item')) == 0, \
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
                assert ref.startswith('arguments.'), \
                    f'Sub_folder ref must be from `item` or `arguments`. Not: {ref}'
                assert len(ref_list) == 2, \
                    'Sub_folder ref must follow format `arguments.<var-name>`. ' \
                    f'Not {ref}'
                # Check parameter is set
                find_io_by_name(arguments, ref_list[1])
        return v

    @validator('arguments', always=True)
    def set_default_args(cls, v):
        return [] if v is None else v

    @validator('returns', always=True)
    def set_default_returns(cls, v):
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

    def check_template(self, template):
        """A function to check the inputs and outputs of a DAG task.

        The DAG tasks should match a certain template.

        Arguments:
            template {Union[DAG, Function]} -- A DAG or Function template

        Raises:
            AssertionError: The task input and output values do not match the task
                template.
        """

        # check all required inputs for template are provided
        arg_names = [argument.name for argument in self.arguments]

        # TODO: add additional check for argument type to match
        for inp in template.inputs:
            if not inp.required:
                # not a required input
                continue
            assert inp.name in arg_names, \
                f'Validation Error for Task {self.name} and Template {template.name}:' \
                f'\n\tMissing required task input from arguments: {inp.name}'

        # check template has the outputs that are requested by this task
        output_names = [output.name for output in template.outputs]
        for ret in self.returns:
            assert ret.name in output_names, \
                f'Validation Error for Task {self.name} and Template {template.name}:' \
                f'\n\tInvalid task return: {ret.name}. {template.name} does not have ' \
                'an output wit this name.'

    @staticmethod
    def artifacts_by_ref_source(artifacts, source) -> List[TaskArguments]:
        """Retrieve a list of argument artifacts by their source type.

        Arguments:
            source {str} -- The source type, one of: 'dag', 'task', 'value'. dag refers
                to InputFileReference, InputFolderReference and InputPathReference.
                'task' refers to TaskFileReference, TaskFolderReference and
                TaskPathReference. Finally 'value' refers to ValueFileReference and
                ValueFolder Reference.

        Raises:
            ValueError: The source type is not recognized

        Returns:
            List[TaskArguments] -- A list of Argument Artifacts
        """
        if not artifacts:
            return []

        if source == 'dag':
            source_class = (InputFileReference, InputFolderReference, InputPathReference)
        elif source == 'task':
            source_class = (TaskFileReference, TaskFolderReference, TaskPathReference)
        elif source == 'value':
            source_class = (ValueFileReference, ValueFolderReference)
        else:
            raise ValueError(
                'reference source string should be one of ["dag", "task" or "value"], '
                f'not {source}'
            )

        return [x for x in artifacts if isinstance(x.from_, source_class)]

    @staticmethod
    def parameters_by_ref_source(parameters, source) -> List[TaskArguments]:
        """Retrieve an list of argument parameters by their source type.

        Arguments:
            source {str} -- The source type, one of: 'dag', 'task', 'item', 'value'

        Raises:
            ValueError: The source type is not recognized

        Returns:
            List[TaskArguments] -- A list of Argument Parameters
        """
        if parameters is None:
            return []

        source_class = None

        if source == 'dag':
            source_class = InputReference
        elif source == 'task':
            source_class = TaskReference
        elif source == 'item':
            source_class = ItemReference
        elif source == 'value':
            source_class = ValueReference
        else:
            raise ValueError(
                'reference source string should be one of ["dag", "task", "item", '
                f'"value"] not {source}'
            )

        return [x for x in parameters if isinstance(x.from_, source_class)]