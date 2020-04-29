from typing import Dict
from pydantic import Field

from ..recipe import BakedRecipe
from .arguments import Arguments


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
