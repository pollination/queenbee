import re
from enum import Enum
from typing import List, Union
from pydantic import Field

from ..base.basemodel import BaseModel


def template_string(keys: List[str]) -> str:
    """Generate a template string from a list of key

    Arguments:
        keys {List[str]} -- A list of keys

    Returns:
        str -- A template string
    """
    return f'{{{{{".".join(keys)}}}}}'


class BaseReference(BaseModel):
    """A Base reference model"""

    @property
    def source(self):
        return None

    def fetch_from_flow(self, flow):
        pass


class FolderArtifactReference(BaseReference):

    type: Enum('FolderReference', {'type': 'folder'}) = 'folder'

    path: str = Field(
        ...,
        description='The path to the file or folder relative to the workflow output folder'
    )


class InputBaseReference(BaseReference):
    """An Input Reference"""

    type: Enum('InputReference', {'type': 'inputs'}) = 'inputs'

    variable: str = Field(
        ...,
        description='The name of the DAG input variable'
    )

    def to_ref_string(self) -> str:
        """Generate a reference string from an input reference

        Returns:
            str -- A reference string
        """
        template = [self.type.value, self.source, self.variable]
        return template_string(template)


class InputArtifactReference(InputBaseReference):
    """An Input Artifact Reference"""

    @property
    def source(self):
        return 'artifacts'


class InputParameterReference(InputBaseReference):
    """An Input Parameter Reference"""

    @property
    def source(self):
        return 'parameters'


class TaskBaseReference(BaseReference):
    """A Task Reference"""

    type: Enum('TaskReference', {'type': 'tasks'}) = 'tasks'

    name: str = Field(
        ...,
        description='The name of the task to pull output data from'
    )

    variable: str = Field(
        ...,
        description='The name of the task output variable'
    )

    def to_ref_string(self) -> str:
        """Generate a reference string from a task reference

        Returns:
            str -- A reference string
        """
        template = [self.type.value, self.name,
                    'outputs', self.source, self.variable]
        return template_string(template)


class TaskArtifactReference(TaskBaseReference):
    """A Task Artifact Reference"""

    @property
    def source(self):
        return 'artifacts'


class TaskParameterReference(TaskBaseReference):
    """A Task Parameter Reference"""

    @property
    def source(self):
        return 'parameters'


class ItemBaseReference(BaseReference):
    """An Item Reference."""

    type: Enum('ItemReference', {'type': 'item'}) = 'item'

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
        template = [self.type.value, self.source, self.variable]
        return template_string(template)


class ItemParameterReference(ItemBaseReference):
    """An Item Parameter Reference"""

    @property
    def source(self):
        return 'parameters'


def references_from_string(string: str) -> List[Union[InputParameterReference, TaskParameterReference, ItemParameterReference]]:
    """Generate a reference object from a reference string

    Arguments:
        string {str} -- A reference string (eg: `{{inputs.parameters.example}}`)

    Raises:
        ValueError: Input string cannot be parsed as a reference object

    Returns:
        List[Union[InputParameterReference, TaskParameterReference, ItemParameterReference]] -- A list of reference objects
    """
    pattern = r"{{\s*([_a-zA-Z0-9.\-\$#\?]*)\s*}}"
    match = re.findall(pattern, string, flags=re.MULTILINE)

    refs = []

    for ref in match:
        split_ref = ref.split('.')
        ref_type = split_ref[0]

        if ref_type == 'input':
            assert len(split_ref) == 2, \
                ValueError(
                    f'Input Reference should be in format "input.variable" but found:'
                    f' {ref}'
            )
            ref = InputParameterReference(variable=split_ref[1])
        elif ref_type == 'tasks':
            assert len(split_ref) == 3, \
                ValueError(
                    f'Task Reference should be in format "tasks.task-name.variable" but'
                    f' found: {ref}'
            )
            ref = TaskParameterReference(
                name=split_ref[1], variable=split_ref[2])
        elif ref_type == 'item':
            variable = '.'.join(split_ref[1:])
            ref = ItemParameterReference(variable=variable)
        else:
            raise ValueError(f'Ref of type {ref_type} not recognized: {ref}')

        refs.append(ref)

    return refs
