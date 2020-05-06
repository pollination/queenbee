from typing import Dict
from pydantic import Field, validator

from ..recipe import BakedRecipe
from .arguments import Arguments, ArgumentParameter, ArgumentArtifact


class Workflow(BakedRecipe):

    labels: Dict = Field(
        None,
        description='Optional user data as a dictionary. User data is for user reference'
        ' only and will not be used in the execution of the workflow.'
    )

    arguments: Arguments = Field(
        None,
        description='Input arguments for this workflow'
    )

    @validator('arguments', always=True)
    def check_entrypoint_inputs(cls, v, values):
        flow = values.get('flow')
        digest = values.get('digest')

        dag = cls.dag_by_name(flow, f'{digest}/main')

        artifacts = v.artifacts
        parameters = v.parameters

        if dag.inputs is not None:
            for parameter in dag.inputs.parameters:
                if parameter.required:
                    exists = next(filter(lambda x: x.name == parameter.name, parameters), None)
                    assert exists is not None, ValueError(f'Workflow must provide argument for parameter {parameter.name}')
            
            for artifact in dag.inputs.artifacts:
                exists = next(filter(lambda x: x.name == artifact.name, artifacts), None)
                assert exists is not None, ValueError(f'Workflow must provide argument for artifact {artifact.name}')

        return v


    @classmethod
    def from_baked_recipe(
        cls,
        recipe: BakedRecipe,
        arguments: Arguments = Arguments(),
        labels: Dict = {}
    ):
        input_dict = recipe.to_dict()
        input_dict['arguments'] = arguments.to_dict()
        input_dict['labels'] = labels

        return cls.parse_obj(input_dict)


