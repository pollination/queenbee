"""Queenbee workflow class.

Workflow is a collection of operators and inter-related tasks that describes an end to
end steps for the workflow.
"""
from uuid import UUID, uuid4
import collections
import json
import os
import re
from graphviz import Digraph
from pydantic import Field, validator, constr
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

    artifact_locations: List[
        Union[RunFolderLocation, InputFolderLocation, HTTPLocation, S3Location]
    ] = Field(
        None,
        description="A list of artifact locations which can be used by child flow objects"
    )

    @validator('artifact_locations', each_item=False)
    def check_duplicate_run_folders(cls, v):
        count = sum(1 if location.type == 'run-folder' else 0 for location in v)
        assert count <= 1, \
            f'Workflow can only have 1 run-folder artifact location. Found {count}'
        return v

    @validator('templates', each_item=False)
    def check_duplicate_template_name(cls, v):
        template_names = [t.name for t in v]
        u_template_names = list(set(template_names))
        if len(template_names) != len(u_template_names):
            # there are duplicate items
            dup = [t for t, c in collections.Counter(template_names).items() if c > 1]
            raise ValueError(
                'Each template name must be unique.'
                f' Duplicate template names: {dup}'
            )
        return v

    @validator('flow')
    def check_templates(cls, v, values):
        """Check template references in flow to ensure they exist."""
        template_names = set(t.name for t in values['templates'])
        invalid_names = [
            task.template for task in v.tasks
            if task.template not in template_names
        ]
        if invalid_names:
            raise ValueError(f'Found invalid template names in flow: {invalid_names}')
        return v

    @validator('flow')
    def check_dependencies(cls, v):
        """Check dependency references in flow to ensure they exist."""
        task_names = set(t.name for t in v.tasks)
        invalid_names = []
        for task in v.tasks:
            dependencies = task.dependencies
            if not dependencies:
                continue
            for dependency in dependencies:
                if dependency not in task_names:
                    invalid_names.append(dependency)
        if invalid_names:
            raise ValueError(
                f'Invalid dependency names in flow tasks: {invalid_names}')
        return v

    # TODO: Remove validate_all and add it as a root_validator
    def validate_all(self):
        """Check that all elements of the workflow are valid together."""
        self.check_artifact_references()

    def check_artifact_references(self):
        """Check artifact references.

        This method check weather any artifact location that is referenced in templates
        or flows exists in artifact_locations.
        """
        values = self.dict()
        v = values.get('artifact_locations')
        if v != None:
            locations = [x.get('name') for x in v]
            artifacts = self.artifacts
            sources = set(artifact.location for artifact in artifacts)
            for source in sources:
                if source not in locations:
                    raise ValueError(
                        'Artifact with location \"{}\" is not valid because it is not'
                        ' listed in the artifact_locations object.'.format(
                            source)
                    )

        return values

    def to_diagraph(self, filename=None):
        """Return a graphviz instance of a diagraph from workflow."""
        if filename is None:
            filename = self.id
        f = Digraph(self.name, filename='{}.gv'.format(filename))

        for task in self.flow.tasks:
            if task.dependencies is not None:
                for dep in task.dependencies:
                    f.edge(dep, task.name)

        return f

    def fetch_workflow_values(self, input_string):
        """Get referenced template value from workflow level value.

        This method returns a dictionary where the keys are the workflow variables in
        input_string and values are the fetched values from workflow. 
        """
        references = parse_double_quote_workflow_vars(input_string)
        if not references:
            return {}
        values = {}
        for ref in references:
            try:
                _, attr, prop, name = ref.split('.')
            except ValueError:
                *_, name = ref.split('.')
                if name == 'id':
                    values[ref] = self.id
                elif name == 'name':
                    values[ref] = self.name
            else:
                if attr in ('inputs', 'outputs'):
                    if prop == 'parameters':
                        values[ref] = self.inputs.get_parameter_value(name)
                    elif prop == 'artifacts':
                        values[ref] = self.inputs.get_artifact_value(name)
                elif attr == 'operators':
                    values[ref] = self.get_operator(prop).image
                else:
                    raise ValueError(
                        f'Invalid workflow variable: {ref}. '
                        f'Variable type must be "parameters", "artifacts" '
                        f'or "operators" not "{attr}"'
                    )

        return values

    def hydrate_workflow_templates(self):
        """Find and replace {{workflow.x.y.z}} variables with input values.

        This method returns the workflow as a dictionary with {{workflow.x.y.z}}
        variables replaced by workflow input values.
        """
        return hydrate_templates(self, wf_value=self.dict(exclude_unset=True))

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

    @property
    def artifacts(self):
        """List of workflow artifacts."""
        artifacts = []
        # collect all artifacts
        for template in self.templates:
            artifacts.extend(template.artifacts)

        for task in self.flow.tasks:
            args = task.arguments
            if not args:
                continue
            if not args.artifacts:
                continue
            artifacts.extend(args.artifacts)

        if self.inputs and self.inputs.artifacts:
            artifacts.extend(self.inputs.artifacts)

        if self.outputs and self.outputs.artifacts:
            artifacts.extend(self.outputs.artifacts)

        return list(artifacts)

    def get_operator(self, name):
        """Get operator by name."""
        operator = [op for op in self.operators if op.name == name]
        if not operator:
            raise ValueError(f'Invalid operator name: {name}')
        return operator[0]


def hydrate_templates(workflow, wf_value=None):
    """Replace all ``{{ workflow.x.y.z }}`` variables with corresponding values.

    Cycle through an arbitrary workflow value (dictionary, list, string etc...) 
    and hydrate any workflow template value with it's actual value. This function 
    should mostly be used by the plugin libraries when converting a queenbee 
    workflow to their own job scheduling language. As such the workflow should 
    contain all the required variable values indicated by a ``{{ workflow.x.y...z }}``.

    In most cases you should use Workflow's ``hydrate_workflow_templates`` method instead
    of using this function directly.
    """
    if isinstance(wf_value, list):
        wf_value = [hydrate_templates(workflow, item) for item in wf_value]

    elif isinstance(wf_value, str):
        "{{workflow.id}}_{{workflow.name}}"
        "{{workflow.id}}"
        values = workflow.fetch_workflow_values(wf_value)

        if values == {}:
            pass

        elif len(values.keys()) == 1:
            for match_k, match_v in values.items():
                assert match_v is not None, \
                    "{{%s}} cannot reference an empty or null value." % (
                        match_k)

                pattern = r"^\s*{{\s*" + match_k + r"\s*}}\s*$"

                # if match is not None then it means that the string value
                # "{{ workflow.key }}" does not require string replace values like the
                # following example: "{{ workflow.id }}-{{ workflow.name }}"
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


# required for self.referencing model
# see https://pydantic-docs.helpmanual.io/#self-referencing-models
Workflow.update_forward_refs()
