import re
from enum import Enum
from typing import List, Union
from pydantic import Field

from ..base.basemodel import BaseModel

def template_string(keys: list) -> str:
    return f'{{{{{".".join(keys)}}}}}'

class BaseReference(BaseModel):

    @property
    def source(self):
        return None

    def fetch_from_flow(self, flow):
        pass


class InputBaseReference(BaseReference):

    type: Enum('InputReference', {'type': 'inputs'}) = 'inputs'

    variable: str = Field(
        ...,
        description='The name of the DAG input variable'
    )

    def to_ref_string(self):
        template = [self.type, self.source, self.variable]
        return template_string(template)

class InputArtifactReference(InputBaseReference):

    @property
    def source(self):
        return 'artifacts'


class InputParameterReference(InputBaseReference):

    @property
    def source(self):
        return 'parameters'


class TaskBaseReference(BaseReference):

    type: Enum('TaskReference', {'type': 'tasks'}) = 'tasks'

    name: str = Field(
        ...,
        description='The name of the task to pull output data from'
    )

    variable: str = Field(
        ...,
        description='The name of the task output variable'
    )

    def to_ref_string(self):
        template = [self.type, self.source, self.name, self.variable]
        return template_string(template)


class TaskArtifactReference(TaskBaseReference):

    @property
    def source(self):
        return 'artifacts'


class TaskParameterReference(TaskBaseReference):

    @property
    def source(self):
        return 'parameters'



class ItemBaseReference(BaseReference):

    type: Enum('ItemReference', {'type': 'item'}) = 'item'

    variable: str = Field(
        None,
        description='The name of the looped item variable (use dot notation for nested json values)'
    )

    def to_ref_string(self):
        template = [self.type, self.source, self.variable]
        return template_string(template)


class ItemParameterReference(ItemBaseReference):

    @property
    def source(self):
        return 'parameters'



def references_from_string(string: str) -> List[Union[InputParameterReference, TaskParameterReference, ItemParameterReference]]:
    pattern = r"{{\s*([_a-zA-Z0-9.\-\$#\?]*)\s*}}"
    match = re.findall(pattern, string, flags=re.MULTILINE)

    refs = []

    for ref in match:
        split_ref = ref.split('.')
        ref_type = split_ref[0]


        if ref_type == 'input':
            assert len(split_ref) == 2, \
                ValueError(f'Input Reference should be in format "input.variable" but found : {ref}')
            ref = InputParameterReference(variable=split_ref[1])
        elif ref_type == 'tasks':
            assert len(split_ref) == 3, \
                ValueError(f'Task Reference should be in format "tasks.task-name.variable" but found : {ref}')
            ref = TaskParameterReference(name=split_ref[1], variable=split_ref[2])
        elif ref_type == 'item':
            variable = '.'.join(split_ref[1:])
            ref = ItemParameterReference(variable=variable)
        else:
            raise ValueError(f'Ref of type {ref_type} not recognized: {ref}')
        
        refs.append(ref)

    
    return refs