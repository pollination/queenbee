from typing import Dict, List
from pydantic import Field, constr

from ..base.basemodel import BaseModel
from ..io.inputs.job import JobArguments


class Job(BaseModel):
    """Queenbee Job.

    A Job is an object to submit a list of arguments to execute a Queenbee recipe.
    """
    api_version: constr(regex='^v1beta1$') = Field('v1beta1', readOnly=True)

    type: constr(regex='^Job$') = 'Job'

    source: str = Field(
        ...,
        description='The source url for downloading the recipe.'
    )

    arguments: List[JobArguments] = Field(
        None,
        description='Input arguments for this job.'
    )

    name: str = Field(
        None,
        description='An optional name for this job. This name will be used a the '
        'display name for the run.'
    )

    description: str = Field(
        None,
        description='Run description.'
    )

    labels: Dict[str, str] = Field(
        None,
        description='Optional user data as a dictionary. User data is for user reference'
        ' only and will not be used in the execution of the job.'
    )
