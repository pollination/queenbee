"""Queenbee workflow class.

Workflow is a collection of operators and inter-related tasks that describes an end to
end steps for the workflow.
"""
from queenbee.schema.qutil import BaseModel
from pydantic import Field, validator, constr, root_validator
from typing import List, Union
from uuid import UUID, uuid4
import json
import os
from queenbee.schema.dag import DAG
from queenbee.schema.arguments import Arguments
from queenbee.schema.operator import Operator
from queenbee.schema.function import Function
from queenbee.schema.artifact_location import LocalLocation, HTTPLocation, S3Location


class Workflow(BaseModel):
    """A DAG Workflow."""

    type: constr(regex='^workflow$')

    name: str

    id: str = str(uuid4())

    inputs: Arguments = Field(
        None
    )

    operators: List[Operator]

    templates: List[Union[Function, DAG, 'Workflow']]

    flow: DAG = Field(
        ...,
        description='A list of steps for using tasks in a DAG workflow'
    )

    outputs: Arguments = Field(
        None
    )

    artifact_locations: List[Union[LocalLocation, HTTPLocation, S3Location]] = Field(
        None,
        description="A list of artifact locations which can be used by child flow objects"
    )

    # @validator('artifact_locations', each_item=True)
    @root_validator
    def check_references_exist(cls, values):
        """Check that any artifact location referenced in templates or flows exists in artifact_locations"""
        v = values.get('artifact_locations')
        if v != None:
            locations = [x.name for x in v]
            artifacts = list_artifacts(values)
            sources = list(set([x.location for x in artifacts]))
            for source in sources:
                if source not in locations:
                    raise ValueError("Artifact with location \"{}\" is not valid because it is not listed in the artifact_locations object.".format(source))

        return values
    # TODO: add a validator to ensure all the names for templates are unique
    # @validator('flow')
    # def check_templates(cls, v, values):
    #     """Check templates in flow to ensure they exist."""
    #     template_names = set(t.name for t in values['templates'])
    #     for task in v.tasks:
    #         if task.template not in template_names:
    #             raise ValueError('{} is not a valid template.'.format(task.template))

    def visualize(self):
        """Visualize workflow."""
        # get data for links and nodes
        data = self.nodes_links
        # write force_layout.js
        directory = os.path.dirname(__file__)
        os.chdir(directory)

        with open('./chart/force_layout.js', 'w') as fl, \
                open('./chart/lib/force_layout') as inf:
            fl.write('data = ' + json.dumps(data))
            fl.write('\n')
            for line in inf:
                fl.write(line)

        # call index.html
        os.system(os.path.join(directory, 'chart/index.html'))

    @property
    def nodes_links(self):
        """Get nodes and links for workflow visualization."""
        task_names = [task.name for task in self.flow.tasks]
        nodes = [{'name': name} for name in task_names]
        links = []
        for count, task in enumerate(self.flow.tasks):
            for source in task.dependencies:
                links.append({'source': task_names.index(source), 'target': count})

        return {'nodes': nodes, 'links': links}


def list_artifacts(obj):
    artifacts = []
    
    if 'flow' in obj:
        for dag in obj['flow']:
            artifacts += list_artifacts(dag)
    
    if 'templates' in obj:
        for template in obj['templates']:
            artifacts += list_artifacts(template)
    
    if isinstance(obj, DAG):
        for task in obj.tasks:
            if 'arguments' in task and 'artifacts' in task.arguments:
                artifacts = artifacts + task.arguments.artifacts  
    
    if isinstance(obj, Function):
        if obj.inputs != None and obj.inputs.artifacts != None:
            artifacts = artifacts + obj.inputs.artifacts
        if obj.outputs != None and obj.outputs.artifacts != None:
            artifacts = artifacts + obj.outputs.artifacts
    
    return artifacts

# required for self.referencing model
# see https://pydantic-docs.helpmanual.io/#self-referencing-models
Workflow.update_forward_refs()
