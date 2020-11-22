import json
import argparse

from pkg_resources import get_distribution
from pydantic_openapi_helper.core import get_openapi
from pydantic_openapi_helper.inheritance import class_mapper
from queenbee.recipe.recipe import Recipe
from queenbee.plugin.plugin import Plugin
from queenbee.workflow.workflow import Workflow


parser = argparse.ArgumentParser(description='Generate OpenAPI JSON schemas')

parser.add_argument('--version',
                    help='Set the version of the new OpenAPI Schema')

args = parser.parse_args()

VERSION = None

if args.version:
    VERSION = args.version.replace('v', '')
else:
    VERSION = '.'.join(get_distribution('queenbee').version.split('.')[:3])


info = {
    "description": "",
    "version": VERSION,
    "title": "",
    "contact": {
        "name": "Ladybug Tools",
        "email": "info@ladybug.tools",
        "url": "https://github.com/ladybug-tools/queenbee"
    },
    "x-logo": {
        "url": "https://www.ladybug.tools/assets/img/honeybee.png",
        "altText": "Queenbee logo"
    },
    "license": {
        "name": "MIT",
        "url": "https://github.com/ladybug-tools/queenbee-schema/blob/master/LICENSE"
    }
}


modules = [
    {'module': [Workflow], 'name': 'Workflow'},
    {'module': [Recipe], 'name': 'Recipe'},
    {'module': [Plugin], 'name': 'Plugin'},
    {'module': [Recipe, Plugin, Workflow], 'name': 'Queenbee'}
]


for module in modules:
    # generate Recipe open api schema
    print(f'Generating {module["name"]} documentation...')

    external_docs = {
        "description": "OpenAPI Specification with Inheritance",
        "url": f"./{module['name'].lower()}_inheritance.json"
    }

    openapi = get_openapi(
        module['module'],
        title=f'Queenbee {module["name"]} Schema',
        description=f'Documentation for Queenbee {module["name"].lower()} schema.',
        version=VERSION, info=info,
        external_docs=external_docs)
    with open(f'./docs/{module["name"].lower()}.json', 'w') as out_file:
        json.dump(openapi, out_file, indent=2)

    # with inheritance
    openapi = get_openapi(
        module['module'],
        title=f'Queenbee {module["name"]} Schema',
        description=f'Documentation for Queenbee {module["name"].lower()} schema.',
        version=VERSION, info=info,
        inheritance=True,
        external_docs=external_docs
    )
    with open(f'./docs/{module["name"].lower()}_inheritance.json', 'w') as out_file:
        json.dump(openapi, out_file, indent=2)

    # add the mapper file
    with open(f'./docs/{module["name"].lower()}_mapper.json', 'w') as out_file:
        json.dump(
            class_mapper(module['module'], ['queenbee', 'queenbee.interface']),
            out_file, indent=2
        )
