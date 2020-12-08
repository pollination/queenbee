import warnings
from typing import Dict, List
from pydantic import Field, validator, constr

from ..base.basemodel import BaseModel
from ..base.metadata import MetaData
from ..recipe import BakedRecipe
from ..io.inputs.submission import SubmissionArguments


class SimulationSubmission(BaseModel):
    """Queenbee Simulation Submission object.

    A Simulation submission is a Baked Recipe with the arguments that will be used to
    execute the recipe as a simulation.
    """
    type: constr(regex='^SimulationSubmission$') = 'SimulationSubmission'

    recipe: BakedRecipe = Field(
        ...,
        description='The baked recipe to be used by the execution engine to generate a '
        'simulation.'
    )

    labels: Dict = Field(
        None,
        description='Optional user data as a dictionary. User data is for user reference'
        ' only and will not be used in the execution of the simulation.'
    )

    arguments: List[SubmissionArguments] = Field(
        None,
        description='Input arguments for this simulation.'
    )

    @validator('arguments', always=True)
    def check_entrypoint_inputs(cls, v, values):
        """Check the arguments match the recipe entrypoint inputs"""
        # replace a None argument with an empty list
        if v is None:
            return []

        recipe = values.get('recipe')

        recipe_inputs = {inp.name: inp for inp in recipe.inputs}
        workflow_args = {inp.name: inp for inp in v}

        if not recipe_inputs:
            return v

        # check provided values against DAG's inputs
        # 1. ensure all the required values are provided.
        # 2. test the input against the spec and make sure it is valid.
        for name, inp in recipe_inputs.items():
            if not inp.required:
                continue
            if name not in workflow_args:
                raise ValueError(
                    f'Value for required input "{name}" is missing from workflow input'
                    ' arguments.'
                )

        valid_args = []
        for name, arg in workflow_args.items():
            if name not in recipe_inputs:
                # argument provided which is not an input for DAG. We can just ignore it.
                warnings.warn(
                    f'No input with name "{name}". The input value will be ignored.'
                )
                continue
            # if arg.is_parameter:
            #     recipe_inputs[name].validate_spec(arg.value)
            # elif arg.source.type == 'ProjectFolder':
            #     recipe_inputs[name].validate_spec(arg.source.path)
            valid_args.append(arg)

        return valid_args

    @classmethod
    def from_baked_recipe(
        cls,
        recipe: BakedRecipe,
        arguments: List[SubmissionArguments] = [],
        labels: Dict = {}
    ):
        """Generate a simulation from a Baked Recipe

        Arguments:
            recipe {BakedRecipe} -- A Baked Recipe

        Keyword Arguments:
            arguments {Arguments} -- Workflow arguments (default: {[]})
            labels {Dict} -- A dictionary of labels used to mark/differentiate a workflow
                (default: {{}})

        Returns:
            Workflow -- A workflow object
        """
        return cls(recipe=recipe, labels=labels, arguments=arguments)


class SubmissionInfo(BaseModel):
    """Simulation submission information.

    This object includes minimum information for submitting a simulation.
    """
    type: constr(regex='^SimulationSubmission$') = 'SimulationSubmission'

    metadata: MetaData = Field(
        ...,
        description='Recipe metadata.'
    )

    arguments: List[SubmissionArguments]

    @classmethod
    def from_simulation_submission(cls, submission: SimulationSubmission):
        """Create simulation submission info from Simulation object."""
        return cls(
            metadata=submission.recipe.metadata,
            arguments=submission.arguments
        )
