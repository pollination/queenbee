from typing import Dict
from pydantic import Field, validator

from ..base.basemodel import BaseModel
from ..recipe import BakedRecipe
from .arguments import Arguments
from .status import WorkflowStatus


class Workflow(BaseModel):
    """Queenbee Workflow.

    A Workflow is a Baked Recipe with some arguments that will be used to execute the
    recipe.
    """

    recipe: BakedRecipe = Field(
        ...,
        description='The baked recipe to be used by the execution engine to generate a '
        'workflow'
    )

    labels: Dict = Field(
        None,
        description='Optional user data as a dictionary. User data is for user reference'
        ' only and will not be used in the execution of the workflow.'
    )

    arguments: Arguments = Field(
        None,
        description='Input arguments for this workflow'
    )

    status: WorkflowStatus = Field(
        None,
        description='The status of the workflow'
    )

    @validator('arguments', always=True)
    def check_entrypoint_inputs(cls, v, values):
        """Check the arguments match the recipe entrypoint inputs"""

        recipe = values.get('recipe')

        recipe_inputs = recipe.inputs

        if recipe_inputs is not None:

            artifacts = []
            parameters = []

            if v is None:
                return Arguments()

            artifacts = v.artifacts
            parameters = v.parameters

            for parameter in recipe_inputs.parameters:
                if parameter.required:
                    exists = next(
                        filter(lambda x: x.name == parameter.name, parameters), None
                    )
                    assert exists is not None, \
                        ValueError(
                            f'Workflow must provide argument for parameter'
                            f' {parameter.name}'
                        )

            for artifact in recipe_inputs.artifacts:
                exists = next(filter(lambda x: x.name == artifact.name, artifacts), None)
                assert exists is not None, \
                    ValueError(
                        f'Workflow must provide argument for artifact {artifact.name}'
                    )

        return v

    @classmethod
    def from_baked_recipe(
        cls,
        recipe: BakedRecipe,
        arguments: Arguments = Arguments(),
        labels: Dict = {}
    ):
        """Generate a workflow from a Baked Recipe

        Arguments:
            recipe {BakedRecipe} -- A Baked Recipe

        Keyword Arguments:
            arguments {Arguments} -- Workflow arguments (default: {Arguments()})
            labels {Dict} -- A dictionary of labels used to mark/differentiate a workflow
                (default: {{}})

        Returns:
            Workflow -- A workflow object
        """
        input_dict = {
            'recipe': recipe.to_dict(),
            'arguments': arguments.to_dict(),
            'labels': labels,
        }

        return cls.parse_obj(input_dict)
