"""A module to generate OpenAPI and JSONSchemas."""

import json
import os
import argparse

from pkg_resources import get_distribution

from pydantic_openapi_helper.core import get_openapi
from pydantic_openapi_helper.inheritance import class_mapper

from queenbee.repository import RepositoryIndex
from queenbee.job import Job, JobStatus, RunStatus
from queenbee.recipe import Recipe, RecipeInterface
from queenbee.plugin import Plugin

folder = os.path.join(os.path.dirname(__file__), 'docs/_static/schemas')
if not os.path.isdir(folder):
    os.mkdir(folder)


parser = argparse.ArgumentParser(description='Generate OpenAPI JSON schemas')

parser.add_argument('--version', help='Set the version of the new OpenAPI Schema')

args = parser.parse_args()

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

with open(os.path.join(folder, 'job-openapi.json'), 'w') as out_file:
    json.dump(
        get_openapi(
            base_object=[Job, JobStatus, RunStatus], title='Queenbee Job Schema',
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


with open(os.path.join(folder, 'job-schemas-combined.json'), 'w') as out_file:
    from pydantic import BaseModel
    from queenbee.io.inputs.step import StepInputs
    from queenbee.io.outputs.step import StepOutputs
    from typing import List, Union
    class JobSchemas(BaseModel):
        job: Job
        job_status: JobStatus
        run_status: RunStatus
        results: List[Union[StepInputs, StepOutputs]]

    out_file.write(JobSchemas.schema_json())

with open(os.path.join(folder, 'job-schema.json'), 'w') as out_file:
    out_file.write(Job.schema_json())

with open(os.path.join(folder, 'job-status-schema.json'), 'w') as out_file:
    out_file.write(JobStatus.schema_json())

with open(os.path.join(folder, 'run-status-schema.json'), 'w') as out_file:
    out_file.write(RunStatus.schema_json())

with open(os.path.join(folder, 'plugin-schema.json'), 'w') as out_file:
    out_file.write(Plugin.schema_json())

with open(os.path.join(folder, 'recipe-schema.json'), 'w') as out_file:
    out_file.write(Recipe.schema_json())

with open(os.path.join(folder, 'repository-schema.json'), 'w') as out_file:
    out_file.write(RepositoryIndex.schema_json())

# write openapi with inheritance and mapper json files
# these files are mainly used for creating .NET SDK
external_docs = {
    "description": "OpenAPI Specification with Inheritance",
    "url": "./queenbee_inheritance.json"
}

models = [Recipe, Plugin, Job, RepositoryIndex, RecipeInterface, JobStatus, RunStatus]
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
