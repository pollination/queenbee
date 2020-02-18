"""Queenbee Info class.

This object provides metadata information for a workflow.

The specification is designed based on openapi info object:
https://swagger.io/specification/#infoObject
"""

from queenbee.schema.qutil import BaseModel
from pydantic import Field


class Contact(BaseModel):
    """Contact information."""
    name: str = Field(
        ...,
        description='The name of the contact person or organization.'
    )

    url: str = Field(
        None,
        description='The url pointing to the contact information.'
    )

    email: str = Field(
        None,
        description='The email address of the contact person or organization.'
    )


class License(BaseModel):
    """License information for the workflow."""
    name: str = Field(
        ...,
        description='The license name used for the workflow.'
    )

    url: str = Field(
        None,
        description='A URL to the license used for the workflow.'
    )


class Info(BaseModel):
    """Workflow meta data information."""
    description: str = Field(
        None,
        description='A short description of the workflow.'
    )

    contact: Contact = Field(
        None,
        description='The contact information.'
    )

    license: License = Field(
        None,
        description='The license information.'
    )

    version: str = Field(
        None,
        description='The version of the workflow.'
    )
