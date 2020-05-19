"""This module generates the OpenAPI documentation for Queenbee workflow
based on Pydantic implementation.
"""
from pkg_resources import get_distribution
from typing import Dict
from pydantic.schema import schema

from .workflow import Workflow

BASE_OPEN_API = {
    "openapi": "3.0.2",
    "servers": [],
    "info": {
        "description": "This is the documentation for Queenbee Workflow schema.",
        "version": '.'.join(get_distribution('queenbee').version.split('.')[:3]),
        "title": "Queenbee Workflow Schema",
        "contact": {
            "name": "Ladybug Tools",
            "email": "info@ladybug.tools",
            "url": "https://github.com/ladybug-tools/queenbee"
        },
        "x-logo": {
            "url": "https://user-images.githubusercontent.com/2915573/71930319-6986f200-3169-11ea-984d-b0f330cfaaa3.png",
            "altText": "Queenbee logo"
        },
        "license": {
            "name": "MIT",
            "url": "https://github.com/ladybug-tools/queenbee/blob/master/LICENSE"
        }
    },
    "externalDocs": {
        "description": "GitHub Repository",
        "url": "https://github.com/ladybug-tools/queenbee"
    },
    "tags": [],
    "x-tagGroups": [
        {
            "name": "Workflow",
            "tags": []
        }
    ],
    "paths": {},
    "components": {"schemas": {}}
}


def get_openapi(
    *,
    schema_class,
    title: str = None,
    version: str = None,
    openapi_version: str = "3.0.2",
    description: str = None,
) -> Dict:
    """Return Queenbee Workflow Schema as an openapi compatible dictionary."""
    open_api = dict(BASE_OPEN_API)

    open_api['openapi'] = openapi_version

    if title:
        open_api['info']['title'] = title

    if version:
        open_api['info']['version'] = version

    if description:
        open_api['info']['description'] = description

    definitions = schema([schema_class], ref_prefix='#/components/schemas/')

    # goes to tags
    tags = []
    # goes to x-tagGroups['tags']
    tag_names = []

    schemas = definitions['definitions']
    schema_names = list(schemas.keys())
    schema_names.sort()
    for name in schema_names:
        model_name = '%s_model' % name.lower()
        tag_names.append(model_name)
        tag = {
            'name': model_name,
            'x-displayName': name,
            'description': '<SchemaDefinition schemaRef=\"#/components/schemas/%s\" />\n' % name
        }
        tags.append(tag)

    tag_names.sort()
    open_api['tags'] = tags
    open_api['x-tagGroups'][0]['tags'] = tag_names

    open_api['components']['schemas'] = schemas

    return open_api
