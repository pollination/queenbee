from typing import Dict
from pydantic import Field, validator

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

    @validator('arguments')
    def check_entrypoint_inputs(cls, v, values):
        flow = values.get('flow')
        digest = values.get('digest')

        dag = cls.dag_by_name(flow, f'{digest}/main')

        artifacts = v.get('artifacts')
        parameters = v.get('parameters')

        for param in parameters:
            if param.required:
                Arguments._by_name(parameters, param.name)

        for art in artifacts:
            if art.required:
                Arguments._by_name(artifacts, art.name)

        return v
