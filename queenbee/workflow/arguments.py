from typing import Union, List
from pydantic import Field

from ..base.basemodel import BaseModel
from ..base.io import IOBase

from ..recipe.artifact_source import HTTPSource, S3Source, ProjectFolderSource


class ArgumentArtifact(BaseModel):

    name: str = Field(
        ...,
        description='The name of the artifact'
    )

    source: Union[HTTPSource, S3Source, ProjectFolderSource] = Field(
        ...,
        description='The source to pull the artifact from'
    )


class ArgumentParameter(BaseModel):

    name: str = Field(
        ...,
        description='The name of the parameter'
    )

    value: str = Field(
        ...,
        description='The value of the parameter'
    )

class Arguments(IOBase):

    artifacts: List[ArgumentArtifact] = Field(
        None,
        description='A list of input artifacts'
    )

    parameters: List[ArgumentParameter] = Field(
        None,
        description='A list of input parameters'
    )
