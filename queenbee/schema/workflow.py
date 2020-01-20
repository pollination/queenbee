"""Queenbee workflow class.

Workflow is a collection of operators and inter-related tasks that describes an end to
end steps for the workflow.
"""
from uuid import uuid4
import collections
import re
from graphviz import Digraph
from pydantic import Field, validator, constr, root_validator
from typing import List, Union
from queenbee.schema.qutil import BaseModel
from queenbee.schema.dag import DAG
from queenbee.schema.arguments import Arguments
from queenbee.schema.operator import Operator
from queenbee.schema.function import Function
from queenbee.schema.artifact_location import RunFolderLocation, InputFolderLocation, \
    HTTPLocation, S3Location
from queenbee.schema.parser import parse_double_quote_workflow_vars, \
    replace_double_quote_vars
import queenbee.schema.variable as qbvar


class Workflow(BaseModel):
    """A DAG Workflow."""

    type: constr(regex='^workflow$')

    name: str

    id: str = str(uuid4())

    inputs: Arguments = Field(
        None
    )

    operators: List[Operator]

    templates: List[Union[Function, DAG, 'Workflow']] = Field(
        ...,
        description='A list of templates. Templates can be Function, DAG or a Workflow.'
    )

    flow: DAG = Field(
        ...,
        description='A list of tasks to create a DAG workflow.'
    )

    outputs: Arguments = Field(
        None
    )

    artifact_locations: List[
        Union[RunFolderLocation, InputFolderLocation, HTTPLocation, S3Location]
    ] = Field(
        None,
        description='A list of artifact locations which can be used by flow objects.'
    )

    @validator('artifact_locations', each_item=False)
    def check_duplicate_artifact_folders(cls, v):
        count = sum(1 if location.type == 'run-folder' else 0 for location in v)
        assert count <= 1, \
            f'Workflow can only have 1 run-folder artifact location. Found {count}'
        count = sum(1 if location.type == 'input-folder' else 0 for location in v)
        assert count <= 1, \
            f'Workflow can only have 1 input-folder artifact location. Found {count}'
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

    @validator('artifact_locations')
    def check_artifact_references(cls, v, values):
        """Check artifact references.

        This method check weather any artifact location that is referenced in templates
        or flows exists in artifact_locations.
        """
        locations = [x.name for x in v]
        # gat all artifacts
        artifacts = cls._get_artifacts(values)

        sources = set(artifact.location for artifact in artifacts)
        for source in sources:
            if source not in locations:
                raise ValueError(
                    f'Artifact with location "{source}" is not valid because it is not'
                    f' listed in the artifact_locations object.'
                )

        return v

    @staticmethod
    def _get_artifacts(values):
        """Get artifacts from workflow values."""
        artifacts = []

        templates = values.get('templates')
        flow = values.get('flow')

        for template in templates:
            artifacts.extend(template.artifacts)

        for task in flow.tasks:
            args = task.arguments
            if not args:
                continue
            if not args.artifacts:
                continue
            artifacts.extend(args.artifacts)

        inputs = values.get('inputs')
        if inputs and inputs.artifacts:
            artifacts.extend(inputs.artifacts)

        outputs = values.get('outputs')
        if outputs and outputs.artifacts:
            artifacts.extend(outputs.artifacts)

        return artifacts

    # @root_validator(skip_on_failure=True)
    # def check_referenced_values(cls, values):
    #     """Cross-reference check for all the referenced values.

    #     This method ensures:
    #         * All workflow referenced values are available in workflow. This method
    #           doesn't check if the value is assigned as it can be done later by updating
    #           inputs.
    #         * All tasks.TASKNAME.outputs references are valid references in task
    #           template.
    #     """
    #     return values

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
            # validate formatting
            qbvar.validate_ref_variable_format(ref)
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
                    assert name == 'image', \
                        'The only valid value for workflow.operators is image name.'
                    values[ref] = self.get_operator(prop).image
                else:
                    raise ValueError(
                        f'Invalid workflow variable: {ref}. '
                        f'Variable type must be "parameters", "artifacts" '
                        f'or "operators" not "{attr}"'
                    )

        return values

    def update_inputs_values(self, values):
        """Update workflow inputs values from a dictionary.

        The dictionary should have two keys for ``parameters`` and ``artifacts``.
        The values for each key is a dictionary where the key is the name of the
        target variable and value is ``key: value`` that should be updated.

        For instance this input updates the value for workers to 6 and grid-name to
        classroom.

        .. code-block:: python

            {
                'parameters': {
                    'worker': {'value': 6},
                    'grid-name': {'value': 'classroom'}
                }
            }

        """
        if not self.inputs:
            raise ValueError(f'Workflow "{self.name}" has no inputs.')

        if 'parameters' in values:
            for k, v in values['parameters'].items():
                self.inputs.set_parameter_value(k, v)

        if 'artifacts' in values:
            for k, v in values['artifacts'].items():
                self.inputs.set_artifact_value(k, v)

    def hydrate_workflow_templates(self, inputs=None):
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

        return artifacts

    def get_operator(self, name):
        """Get operator by name."""
        operator = [op for op in self.operators if op.name == name]
        if not operator:
            raise ValueError(f'Invalid operator name: {name}')
        return operator[0]

    def get_inputs_parameter(self, name):
        """Get an inputs parameter by name."""
        if self.inputs:
            return self.inputs.get_parameter(name)
        else:
            raise ValueError('Workflow has no inputs.')

    def get_inputs_artifact(self, name):
        """Get an inputs artifact by name."""
        if self.inputs:
            return self.inputs.get_artifact(name)
        else:
            raise ValueError('Workflow has no inputs.')

    def get_outputs_parameter(self, name):
        """Get an outpus parameter by name."""
        if self.outputs:
            return self.outputs.get_parameter(name)
        else:
            raise ValueError('Workflow has no outputs.')

    def get_outputs_artifact(self, name):
        """Get an outputs artifact by name."""
        if self.outputs:
            return self.outputs.get_artifact(name)
        else:
            raise ValueError('Workflow has no outputs.')

    def get_template(self, name):
        """Get template by name."""
        if self.templates:
            template = [t for t in self.templates if t.name == name]
            if not template:
                raise ValueError(f'No template with name: {name}.')
        else:
            raise ValueError(f'Workflow {self.name} has no templates.')

        return template[0]

    def get_task(self, name):
        """Get a task from the flow by name."""
        task = [t for t in self.flow.tasks if t.name == name]
        if not task:
            raise ValueError('No task with name: {name}')
        return task[0]


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

                if isinstance(match_v, list) or isinstance(match_v, dict) or \
                        match is not None:
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
