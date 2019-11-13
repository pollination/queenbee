"""Queenbee ArtifactLocation class.

ArtifactLocation is a configuration to a source system to acquire artifacts from.

Queenbee accepts three types of locations:

    1. Local: The machine where the workflow is running's local file system
    2. HTTP: A web http to a website or an API for example
    3. S3: An S3 bucket
"""
from queenbee.schema.qutil import BaseModel
from pydantic import Schema, constr
from typing import Dict
from enum import Enum


class VerbEnum(str, Enum):
    get = 'GET'
    post = 'POST'
    put = 'PUT'
    patch = 'PATCH'
    delete = 'DELETE'


class ArtifactLocation(BaseModel):
    """ArtifactLocation

    An Artifact Location System
    """

    name: str = Schema(
        ...,
        description='Name is a unique identifier for this particular Artifact Location'
    )

    root: str = Schema(
        ...,
        description="The root path to the artifacts."
    )


class LocalLocation(BaseModel):
    """Local Location

    A folder on a machine's file system. This machine is the one where the workflow is running.
    """
    type: constr(regex='^local$')

    name: str = Schema(
        ...,
        description='Name is a unique identifier for this particular Artifact Location'
    )

    root: str = Schema(
        ...,
        description="For a local filesystem this can be \"C:\\Users\\me\\simulations\\test\"."
    )


class HTTPLocation(BaseModel):
    """HTTPLocation

    A web HTTP to an FTP server or an API for example.
    """

    type: constr(regex='^http$')

    name: str = Schema(
        ...,
        description='Name is a unique identifier for this particular Artifact Location'
    )

    root: str = Schema(
        ...,
        description="For a HTTP endpoint this can be http://climate.onebuilding.org."
    )

    headers: Dict[str, str] = Schema(
        None,
        description="An object with Key Value pairs of HTTP headers"
    )

    verb: VerbEnum = Schema(
        'GET',
        description="The HTTP verb to use when making the request."
    )

    class Config:
        use_enum_value = True


class S3Location(BaseModel):
    """S3Location

    An S3 bucket
    """

    type: constr(regex='^s3$')

    name: str = Schema(
        ...,
        description='Name is a unique identifier for this particular Artifact Location'
    )

    root: str = Schema(
        '/',
        description="The path inside the bucket to source artifacts from."
    )

    endpoint: str = Schema(
        ...,
        description="The HTTP endpoint to reach the S3 bucket."
    )

    bucket: str = Schema(
        ...,
        description="The name of the S3 bucket on the host server."
    )

    credentials_path: str = Schema(
        ...,
        description="Path to the file holding the AccessKey and SecretAccessKey to authenticate to the bucket"
    )
