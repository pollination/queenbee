"""Queenbee ArtifactSource class.

ArtifactSource is a configuration to a source system to acquire artifacts from.

Queenbee accepts three types of locations:

    1. Local: The machine where the workflow is running on local file system
    2. HTTP: A web http to a website or an API for example
    3. S3: An S3 bucket
"""
from typing import Dict, List
from enum import Enum
from pydantic import Field

from ..base.basemodel import BaseModel
from ..base.variable import get_ref_variable

class ArtifactSource(BaseModel):
    """ArtifactSource

    An Artifact Source System.
    """

    @staticmethod
    def _referenced_values(values: list = []) -> Dict[str, List[str]]:
        """Get referenced variables if any"""
        ref_values = {}
        
        if values == []:
            return ref_values

        for value in values:
            if value is None:
                continue
            ref_var = get_ref_variable(value)
            if ref_var:
                ref_values[value] = ref_var

        return ref_values

    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        return self._referenced_values()


class ProjectFolderSource(ArtifactSource):
    """Project Folder Source

    This is the folder a workflow will use as it's root path when running a simulation.
    When run on a local machine (using queenbee-luigi for example) the root path should
    be a path on the user's machine.
    If running on the Pollination platform the `root` value is ignored and the data is
    persisted to a run specific folder in S3 within the Pollination backend.
    """
    type: Enum('ProjectFolderSource', {'type': 'project-folder'})

    path: str = Field(
        None,
        description="For a local filesystem this can be \"C:\\Users\\me\\simulations\\test\".\
            This will correspond to the run specific folder ."
    )

    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        values = [self.path]

        return self._referenced_values(values)


class SimulationFolder(ArtifactSource):
    """Simulation Folder Source to pull artifacts from

    Refer to another simulation on pollination cloud and pull data from its
    project folder. This can be used to loosely chain workflows together.
    """


    type: Enum('SimulationFolder', {'type': 'simulation-folder'})


    workflow_id: str = Field(
        ...,
        description='The ID of the workflow to pull artifacts from'
    )

    path: str = Field(
        ...,
        description='The path to the artifact within the project folder of the referenced workflow'
    )

    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        values = [self.workflow_id, self.path]

        return self._referenced_values(values)

class HTTPSource(ArtifactSource):
    """HTTPSource

    A web HTTP to an FTP server or an API for example.
    """

    type: Enum('HTTPSource', {'type': 'http'})


    url: str = Field(
        ...,
        description="For a HTTP endpoint this can be http://climate.onebuilding.org."
    )

    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        values = [self.url]

        return self._referenced_values(values)


class S3Source(ArtifactSource):
    """S3Source

    An S3 bucket artifact Source
    """

    type: Enum('S3Source', {'type': 's3'})


    key: str = Field(
        ...,
        description="The path inside the bucket to source artifacts from."
    )

    endpoint: str = Field(
        ...,
        description="The HTTP endpoint to reach the S3 bucket."
    )

    bucket: str = Field(
        ...,
        description="The name of the S3 bucket on the host server."
    )

    credentials_path: str = Field(
        None,
        description="Path to the file holding the AccessKey and SecretAccessKey to "
        "authenticate to the bucket. Assumes public bucket access if none are specified."
    )

    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        values = [self.key, self.endpoint, self.bucket, self.credentials_path]

        return self._referenced_values(values)
