"""Queenbee workflow class.

Workflow is a collection of operators and inter-related tasks that describes an end to
end steps for the workflow.
"""
from uuid import UUID, uuid4
import json
import os
import re
from graphviz import Digraph
from pydantic import Schema, validator, constr
from typing import List, Union
from queenbee.schema.qutil import BaseModel
from queenbee.schema.dag import DAG
from queenbee.schema.arguments import Arguments
from queenbee.schema.operator import Operator
from queenbee.schema.function import Function
from queenbee.schema.artifact_location import RunFolderLocation, InputFolderLocation, HTTPLocation, S3Location
from queenbee.schema.parser import parse_double_quote_workflow_vars, replace_double_quote_vars


class Workflow(BaseModel):
    """A DAG Workflow."""

    type: constr(regex='^workflow$')

    name: str

    id: str = str(uuid4())

    inputs: Arguments = Schema(
        None
    )

    operators: List[Operator]

    templates: List[Union[Function, DAG, 'Workflow']]

    flow: DAG = Schema(
        ...,
        description='A list of steps for using tasks in a DAG workflow'
    )

    outputs: Arguments = Schema(
        None
    )

    artifact_locations: List[
        Union[RunFolderLocation, InputFolderLocation, HTTPLocation, S3Location]
        ] = Schema(
        None,
        description="A list of artifact locations which can be used by child flow objects"
    )

    @validator('artifact_locations', whole=True)
    def check_duplicate_run_folders(cls, v):
        count = 0
        for location in v:
            if location.type == 'run-folder':
                count +=1
        assert count <= 1, "Workflow can only have 1 run-folder artifact location"
        return v

    def validate_all(self):
        """Check that all elements of the workflow are valid together"""
        self.check_references_exist()

        for template in self.templates:
            if template.type == 'function':
                template.validate_all()


    def check_references_exist(self):
        """Check that any artifact location referenced in templates or flows exists in artifact_locations"""
        values = self.dict()
        v = values.get('artifact_locations')
        if v != None:
            locations = [x.get('name') for x in v]
            artifacts = list_artifacts(values)
            sources = list(set([x.get('location') for x in artifacts]))
            for source in sources:
                if source not in locations:
                    raise ValueError(
                        "Artifact with location \"{}\" is not valid because it is not listed in the artifact_locations object.".format(source))

        return values

    # TODO: add a validator to ensure all the names for templates are unique
    # @validator('flow')
    # def check_templates(cls, v, values):
    #     """Check templates in flow to ensure they exist."""
    #     template_names = set(t.name for t in values['templates'])
    #     for task in v.tasks:
    #         if task.template not in template_names:
    #             raise ValueError('{} is not a valid template.'.format(task.template))

    def to_diagraph(self, filename=None):
        """Return a graphviz instance of a diagraph from workflow"""
        if filename is None:
            filename = self.id
        f = Digraph(self.name, filename='{}.gv'.format(filename))

        for task in self.flow.tasks:
            if task.dependencies is not None:
                for dep in task.dependencies:
                    f.edge(dep, task.name)

        return f

    def fetch_workflow_values(self, template_string):
        """replaces template value with workflow level value"""
        references = parse_double_quote_workflow_vars(template_string)

        values = {}

        for ref in references:
            keys = ref.split('.')
            obj = self.dict()

            for key in keys[1:]:
                if isinstance(obj, list):
                    obj = list(filter(lambda x: x.get('name') == key, obj))[0]
                else:
                    obj = obj[key]

            values[ref] = obj

        return values

    def hydrate_workflow_templates(self):
        """returns a dictionary version of the workflow with {{workflow.x.y.z}} variables as values"""
        return hydrate_templates(
            self, wf_value=self.dict(skip_defaults=True))

        
    @property
    def nodes_links(self):
        """Get nodes and links for workflow visualization."""
        task_names = [task.name for task in self.flow.tasks]
        nodes = [{'name': name} for name in task_names]
        links = []
        for count, task in enumerate(self.flow.tasks):
            for source in task.dependencies:
                links.append(
                    {'source': task_names.index(source), 'target': count})

        return {'nodes': nodes, 'links': links}


def hydrate_templates(workflow, wf_value=None):
    """Replace all `{{ workflow.x.y.z }}` with corresponding value

    Cycle through an arbitrary workflow value (dictionary, list, string etc...) 
    and hydrate any workflow template value with it's actual value. This command 
    should mostly be used by the plugin libraries when converting a queenbee 
    workflow to their own job scheduling language. As such the workflow should 
    contain all the required variable values indicated by a `{{ workflow.x.y...z }}`.
    """

    if isinstance(wf_value, list):
        wf_value = [hydrate_templates(workflow, item) for item in wf_value]

    elif isinstance(wf_value, str):
        values = workflow.fetch_workflow_values(wf_value)

        if values == {}:
            pass

        elif len(values.keys()) == 1:
            for match_k, match_v in values.items():
                assert match_v is not None, \
                    "{{%s}} cannot reference an empty or null value." % (match_k)

                pattern = r"^\s*{{\s*" + match_k + r"\s*}}\s*$"

                # if match is not None then it means that the string value "{{ workflow.key }}" does not
                # require string replace values like the following example: "{{ workflow.id }}-{{ workflow.name }}"
                match = re.search(pattern, wf_value)

                if isinstance(match_v, list) or isinstance(match_v, dict) or match is not None:
                    wf_value = match_v
                else:
                    wf_value = replace_double_quote_vars(
                        wf_value, match_k, str(match_v))

        else:
            new_v = wf_value
            for match_k, match_v in values.items():
                assert not isinstance(match_v, list) or not isinstance(match_v, dict), \
                    "Cannot concat {{%s}} of type %s into %s" % (
                        match_k, type(match_v), wf_value)
                new_v = replace_double_quote_vars(new_v, match_k, str(match_v))

            wf_value = new_v

    elif isinstance(wf_value, dict):
        for k, v in wf_value.items():
            wf_value[k] = hydrate_templates(workflow, v)

    return wf_value


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
