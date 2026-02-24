"""A module to generate OpenAPI and JSONSchemas."""

import argparse
import json
import os
from typing import List, Union

from importlib.metadata import distribution
from pydantic_openapi_helper.core import get_openapi
from pydantic_openapi_helper.inheritance import class_mapper

from pydantic import BaseModel
from queenbee.job import Job, JobStatus, RunStatus
from queenbee.plugin import Plugin
from queenbee.recipe import Recipe, RecipeInterface
from queenbee.repository import RepositoryIndex
from queenbee.io.inputs.step import StepInputs
from queenbee.io.outputs.step import StepOutputs


folder = os.path.join(os.path.dirname(__file__), '../docs/_static/schemas')
if not os.path.isdir(folder):
    os.mkdir(folder)


parser = argparse.ArgumentParser(description='Generate OpenAPI JSON schemas')

parser.add_argument(
    '--version', help='Set the version of the new OpenAPI Schema')

args = parser.parse_args()

if args.version:
    VERSION = args.version.replace('v', '')
else:
    VERSION = '.'.join(distribution('queenbee').version.split('.')[:3])

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

with open(os.path.join(folder, 'job-openapi.json'), 'w') as out_file:
    json.dump(
        get_openapi(
            base_object=[Job, JobStatus,
                         RunStatus], title='Queenbee Job Schema',
            description='Schema documentation for Queenbee Jobs',
            version=VERSION
        ),
        out_file,
        indent=2
    )

with open(os.path.join(folder, 'plugin-openapi.json'), 'w') as out_file:
    json.dump(
        get_openapi(
            base_object=[Plugin], title='Queenbee Plugin Schema',
            description='Schema documentation for Queenbee Plugins',
            version=VERSION
        ),
        out_file,
        indent=2
    )

with open(os.path.join(folder, 'recipe-openapi.json'), 'w') as out_file:
    json.dump(
        get_openapi(
            base_object=[Recipe], title='Queenbee Recipe Schema',
            description='Schema documentation for Queenbee Recipes',
            version=VERSION
        ),
        out_file,
        indent=2
    )

with open(os.path.join(folder, 'repository-openapi.json'), 'w') as out_file:
    json.dump(
        get_openapi(
            base_object=[RepositoryIndex], title='Queenbee Repository Schema',
            description='Schema documentation for Queenbee Recipes',
            version=VERSION
        ),
        out_file,
        indent=2
    )


def dump_model_schema(model, path):
    with open(path, 'w') as f:
        json.dump(model.model_json_schema(), f, indent=2)

with open(os.path.join(folder, 'job-schemas-combined.json'), 'w') as out_file:
    class JobSchemas(BaseModel):
        job: Job
        job_status: JobStatus
        run_status: RunStatus
        results: List[Union[StepInputs, StepOutputs]]

    json.dump(JobSchemas.model_json_schema(), out_file, indent=2)

dump_model_schema(Job, os.path.join(folder, 'job-schema.json'))
dump_model_schema(JobStatus, os.path.join(folder, 'job-status-schema.json'))
dump_model_schema(RunStatus, os.path.join(folder, 'run-status-schema.json'))
dump_model_schema(Plugin, os.path.join(folder, 'plugin-schema.json'))
dump_model_schema(Recipe, os.path.join(folder, 'recipe-schema.json'))
dump_model_schema(RepositoryIndex, os.path.join(folder, 'repository-schema.json'))


external_docs = {
    "description": "OpenAPI Specification with Inheritance",
    "url": "./queenbee_inheritance.json"
}

models = [Recipe, Plugin, Job, RepositoryIndex,
          RecipeInterface, JobStatus, RunStatus]

openapi = get_openapi(
    models,
    title='Queenbee Schema',
    description='Documentation for Queenbee schema.',
    version=VERSION, info=info,
    external_docs=external_docs
)
with open(os.path.join(folder, 'queenbee.json'), 'w') as out_file:
    json.dump(openapi, out_file, indent=2)

# with inheritance
openapi = get_openapi(
    models,
    title='Queenbee Schema with Inheritance',
    description='Documentation for Queenbee schema.',
    version=VERSION, info=info,
    inheritance=True,
    external_docs=external_docs
)
with open(os.path.join(folder, 'queenbee_inheritance.json'), 'w') as out_file:
    json.dump(openapi, out_file, indent=2)

# add the mapper file
with open(os.path.join(folder, 'queenbee_mapper.json'), 'w') as out_file:
    json.dump(
        class_mapper(
            models,
            ['queenbee', 'queenbee.interface']
        ),
        out_file, indent=2
    )
