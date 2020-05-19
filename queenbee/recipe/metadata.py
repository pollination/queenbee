"""Queenbee Recipe MetaData class.

This object provides metadata information for a recipe.

The specification is designed based on openapi info object:
https://swagger.io/specification/#infoObject
"""

from typing import List
from pydantic import Field

from ..base.basemodel import BaseModel


class Maintainer(BaseModel):
    """Maintainer information"""
    name: str = Field(
        ...,
        description='The name of the author/maintainer person or organization.'
    )

    email: str = Field(
        None,
        description='The email address of the author/maintainer person or organization.'
    )


class License(BaseModel):
    """License information for the Recipe"""
    name: str = Field(
        ...,
        description='The license name used for the recipe.'
    )

    url: str = Field(
        None,
        description='A URL to the license used for the recipe.'
    )


class MetaData(BaseModel):
    """Recipe metadata information."""

    name: str = Field(
        ...,
        description='Recipe name. Make it descriptive and helpful ;)'
    )

    version: str = Field(
        ...,
        description='The version of the recipe'
    )

    keywords: List[str] = Field(
        None,
        description='A list of keywords to search the recipe by'
    )

    maintainers: List[Maintainer] = Field(
        None,
        description='A list of maintainers for the recipe'
    )

    home: str = Field(
        None,
        description='The URL of this recipe\'s home page'
    )

    sources: List[str] = Field(
        None,
        description='A list of URLs to source code for this project'
    )

    icon: str = Field(
        None,
        description='A URL to an SVG or PNG image to be used as an icon'
    )

    deprecated: bool = Field(
        None,
        description='Whether this recipe is deprecated'
    )

    description: str = Field(
        None,
        description='A description of what this recipe does'
    )

    license: License = Field(
        None,
        description='The license information.'
    )
