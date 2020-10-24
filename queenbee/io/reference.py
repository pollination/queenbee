"""Objects to reference parameters, files and folders from inputs, tasks and items."""

import re
from typing import List, Union, Dict, Any
from pydantic import Field, constr, validator

from ..base.basemodel import BaseModel


def template_string(keys: List[str]) -> str:
    """Generate a template string from a list of key

    Arguments:
        keys {List[str]} -- A list of keys

    Returns:
        str -- A template string
    """
    return f'{{{{{".".join(keys)}}}}}'


class _BaseReference(BaseModel):
    """A Base reference model."""

    type: constr(regex='^_BaseReference$') = '_BaseReference'

    @property
    def source(self):
        return None

    def fetch_from_flow(self, flow):
        pass


class FileReference(_BaseReference):
    """Reference to a file."""
    type: constr(regex='^FileReference$') = 'FileReference'

    path: str = Field(
        ...,
        description='Relative path to a file.'
    )


class FolderReference(_BaseReference):
    """Reference to a folder."""
    type: constr(regex='^FolderReference$') = 'FolderReference'

    path: str = Field(
        ...,
        description='Relative path to a folder.'
    )

    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        """Get referenced variables if any.

        Returns:
            Dict[str, List[str]] -- A dictionary where keys are attributes and values
                are lists contain referenced value string.
        """
        return self._referenced_values(['path'])


class _TaskReferenceBase(_BaseReference):
    """A Task Reference"""

    type: constr(regex='^_TaskReferenceBase$') = '_TaskReferenceBase'

    name: str = Field(
        ...,
        description='The name of the task to pull output data from.'
    )

    variable: str = Field(
        ...,
        description='The name of the variable.'
    )

    def to_ref_string(self) -> str:
        """Generate a reference string from a task reference.

        tasks.{task_name}.outputs.{artifacts|parameters}.{variable_name}

        Returns:
            str -- A reference string
        """
        template = ['tasks', self.name, 'outputs', self.source, self.variable]
        return template_string(template)


class TaskFileReference(_TaskReferenceBase):
    """A reference to a file that is generated in a task."""

    type: constr(regex='^TaskFileReference$') = 'TaskFileReference'

    @property
    def source(self):
        return 'artifacts'


class TaskFolderReference(_TaskReferenceBase):
    """A reference to a folder that is generated in a task."""

    type: constr(regex='^TaskFolderReference$') = 'TaskFolderReference'

    @property
    def source(self):
        return 'artifacts'


class TaskPathReference(_TaskReferenceBase):
    """A reference to a file or folder that is generated in a task."""

    type: constr(regex='^TaskPathReference$') = 'TaskPathReference'

    @property
    def source(self):
        return 'artifacts'


class TaskReference(_TaskReferenceBase):
    """A Task reference for parameters other than files or folders."""

    type: constr(regex='^TaskReference$') = 'TaskReference'

    @property
    def source(self):
        return 'parameters'


class _InputReferenceBase(_BaseReference):
    """An input reference."""

    type: constr(regex='^_InputReferenceBase$') = '_InputReferenceBase'

    variable: str = Field(
        ...,
        description='The name of the DAG input variable'
    )

    def to_ref_string(self) -> str:
        """Generate a reference string from an input reference

        Returns:
            str -- A reference string
        """
        template = ['inputs', self.source, self.variable]
        return template_string(template)


class InputReference(_InputReferenceBase):
    """An input parameter reference which is not a file or a folder.

    For a file or a folder use InputFileReference, InputFolderReference or
    InputPathReference instead.
    """

    type: constr(regex='^InputReference$') = 'InputReference'

    @property
    def source(self):
        return 'parameters'


class InputFileReference(_InputReferenceBase):
    """An input file reference"""

    type: constr(regex='^InputFileReference$') = 'InputFileReference'

    @property
    def source(self):
        return 'artifacts'


class InputFolderReference(_InputReferenceBase):
    """An input folder reference"""

    type: constr(regex='^InputFolderReference$') = 'InputFolderReference'

    @property
    def source(self):
        return 'artifacts'


class InputPathReference(_InputReferenceBase):
    """An input file or folder reference"""

    type: constr(regex='^InputPathReference$') = 'InputPathReference'

    @property
    def source(self):
        return 'artifacts'


class ItemReference(_BaseReference):
    """An Item Reference."""

    type: constr(regex='^ItemReference$') = 'ItemReference'

    variable: str = Field(
        None,
        description='The name of the looped item variable (use dot notation for nested'
        ' json values)'
    )

    def to_ref_string(self):
        """Generate a reference string from an item reference

        Returns:
            str -- A reference string
        """
        template = ['item', self.source, self.variable]
        return template_string(template)

    @property
    def source(self):
        return 'parameters'


class ValueReference(_BaseReference):
    """A reference to a fixed value."""

    type: constr(regex='^ValueReference$') = 'ValueReference'

    value: Any = Field(
        ...,
        description='A fixed value for this reference.'
    )


class ValueListReference(_BaseReference):
    """A reference to a fixed value."""

    type: constr(regex='^ValueListReference$') = 'ValueListReference'

    # TODO: Add validation for fixed value reference types.
    value: List[Any] = Field(
        ...,
        description='A fixed value for this reference.'
    )

    @validator('value')
    def check_value(cls, v):
        if v == []:
            raise ValueError(
                'ValueListReference must be a non-empty list or null')
        return v


class ValueFileReference(_BaseReference):
    """A reference to a fixed file."""

    type: constr(regex='^ValueFileReference$') = 'ValueFileReference'

    path: str = Field(
        ...,
        description='A fixed value for this reference.'
    )


class ValueFolderReference(ValueFileReference):
    """A reference to a fixed folder."""

    type: constr(regex='^ValueFolderReference$') = 'ValueFolderReference'


def references_from_string(string: str) -> List[
        Union[InputReference, TaskReference, ItemReference]
        ]:
    """Generate a reference object from a reference string

    Arguments:
        string {str} -- A reference string (eg: `{{inputs.example}}`)

    Raises:
        ValueError: Input string cannot be parsed as a reference object

    Returns:
        List[Union[InputReference, TaskReference, ItemReference]] -- A list of reference objects
    """
    pattern = r"{{\s*([_a-zA-Z0-9.\-\$#\?]*)\s*}}"
    match = re.findall(pattern, string, flags=re.MULTILINE)

    refs = []

    for ref in match:
        split_ref = ref.split('.')
        ref_type = split_ref[0]

        if ref_type == 'input':
            assert len(split_ref) == 2, \
                f'Input Reference must be in formatted as "input.variable" not {ref}.'
            ref = InputReference(variable=split_ref[1])
        elif ref_type == 'tasks':
            assert len(split_ref) == 3, \
                ValueError(
                    f'Task Reference should be in format "tasks.task-name.variable" but'
                    f' found: {ref}'
            )
            ref = TaskReference(
                name=split_ref[1], variable=split_ref[2])
        elif ref_type == 'item':
            variable = '.'.join(split_ref[1:])
            ref = ItemReference(variable=variable)
        else:
            raise ValueError(f'Reference of type {ref_type} not recognized: {ref}')

        refs.append(ref)

    return refs
