"""Queenbee workflow class.

Workflow is a collection of operators and inter-related tasks that describes an end to
end steps for the workflow.
"""
from uuid import uuid4
from enum import Enum
import collections
import re
from graphviz import Digraph
from pydantic import Field, validator, constr, root_validator
from typing import List, Union, Dict


from ..base.basemodel import BaseModel
from ..base.io import IOBase

from ..operator.function import Function
from ..operator.operator import Config

from .dag import DAG
from .metadata import MetaData
from .dependency import Dependency


class TemplateFunction(Function):

    config: Config = Field(
        ...,
        description='The operator config to use for this function'
    )


class Flow(BaseModel):

    entrypoint: str = Field(
        ...,
        description='The name of the main DAG of this flow'
    )

    dags: List[DAG] = Field(
        ...,
        description='A list of DAGs'
    )

    @classmethod
    @root_validator
    def check_entrypoint(cls, values):
        entrypoint = values.get('entrypoint')
        dags = values.get('dags')

        filtered_list = list(filter(lambda x: x.name == entrypoint, dags))

        if len(filtered_list) != 1:
            raise ValueError(
                f'Flow entrypoint "{entrypoint}" should refer to 1 DAG but found: {len(filtered_list)}'
            )

        return values

    @property
    def root_dag(self):
        return list(filter(lambda x: x.name == self.entrypoint, self.dags))[0]


class Recipe(BaseModel):
    """A DAG Workflow."""

    name: str

    metadata: MetaData = Field(
        None,
        description='Workflow metadata information.'
    )

    dependencies: List[Dependency] = Field(
        None,
        description='A list of operators and other workflows this workflow depends on.'
    )

    flow: DAG = Field(
        ...,
        description='A list of tasks to create a DAG workflow.'
    )

    @property
    def inputs(self):
        return self.flow.root_dag.inputs




# This class is used for validation purposes
class BakedRecipe(Recipe):

    # templates only exist in the compiled version of a workflow
    templates: List[Union[TemplateFunction, DAG]] = Field(
        ...,
        description='A list of templates. Templates can be Function or a DAG.'
    )

    @classmethod
    @root_validator
    def validate_templates(cls, values):
        pass



    # @validator('templates', each_item=False)
    # def check_duplicate_template_name(cls, v):
    #     template_names = [t.name for t in v]
    #     u_template_names = list(set(template_names))
    #     if len(template_names) != len(u_template_names):
    #         # there are duplicate items
    #         dup = [t for t, c in collections.Counter(template_names).items() if c > 1]
    #         raise ValueError(
    #             'Each template name must be unique.'
    #             f' Duplicate template names: {dup}'
    #         )
    #     return v

    # @validator('flow')
    # def check_templates(cls, v, values):
    #     """Check template references in flow to ensure they exist."""
    #     template_names = set(t.name for t in values['templates'])
    #     invalid_names = [
    #         task.template for task in v.tasks
    #         if task.template not in template_names
    #     ]
    #     if invalid_names:
    #         raise ValueError(f'Found invalid template names in flow: {invalid_names}')
    #     return v

    # @validator('flow')
    # def check_dependencies(cls, v):
    #     """Check dependency references in flow to ensure they exist."""
    #     task_names = set(t.name for t in v.tasks)
    #     invalid_names = []
    #     for task in v.tasks:
    #         dependencies = task.dependencies
    #         if not dependencies:
    #             continue
    #         for dependency in dependencies:
    #             if dependency not in task_names:
    #                 invalid_names.append(dependency)
    #     if invalid_names:
    #         raise ValueError(
    #             f'Invalid dependency names in flow tasks: {invalid_names}')
    #     return v

#     @staticmethod
#     def _get_artifacts(values):
#         """Get artifacts from workflow values."""
#         artifacts = []

#         templates = values.get('templates')
#         flow = values.get('flow')

#         for template in templates:
#             artifacts.extend(template.artifacts)

#         for task in flow.tasks:
#             args = task.arguments
#             if not args:
#                 continue
#             if not args.artifacts:
#                 continue
#             artifacts.extend(args.artifacts)

#         inputs = values.get('inputs')
#         if inputs and inputs.artifacts:
#             artifacts.extend(inputs.artifacts)

#         outputs = values.get('outputs')
#         if outputs and outputs.artifacts:
#             artifacts.extend(outputs.artifacts)

#         return artifacts

#     @staticmethod
#     def _assert_workflow_values(values, references):

#         # references = parse_double_quote_workflow_vars(input_string)
#         if not references:
#             return True # If parser doesn't return refs then string is not a workflow var

#         for ref in references:
#             # validate formatting
#             qbvar.validate_ref_variable_format(ref)
            
#             # No need to check if it's not a workflow level variable
#             if not ref.startswith('workflow.'):
#                 continue

#             try:
#                 _, attr, prop, name = ref.split('.')
#             except ValueError:
#                 *_, name = ref.split('.')

#                 assert name in ['id', 'name'], ValueError(
#                     f'Invalid workflow variable: {ref}. '
#                     f'Variable type must be "workflow.id", "workflow.name" '
#                     f'not "{attr}"'
#                 )
#             else:
#                 if attr in ('inputs'):
#                     inputs = values.get('inputs')
#                     if prop == 'parameters':
#                         try:
#                             inputs.get_parameter_value(name)
#                         except ValueError as err:
#                             raise ValueError(f'Referenced value does not exist: {ref}')
#                     elif prop == 'artifacts':
#                         try:
#                             inputs.get_artifact_value(name)
#                         except ValueError as err:
#                             raise ValueError(f'Referenced value does not exist: {ref}')
#                 elif attr == 'operators':
#                     assert name == 'image', \
#                         ValueError('The only valid value for workflow.operators is image name.')
#                     operator = [op for op in values.get('operators') if op.name == name]
#                     if not operator:
#                         raise ValueError(
#                             'Invalid operator name. Operator does not exist in '
#                             f'the workflow definition: {name}'
#                         )
#                 else:
#                     raise ValueError(
#                         f'Invalid workflow variable: {ref}. '
#                         f'Variable type must be "parameters", "artifacts" '
#                         f'or "operators" not "{attr}"'
#                     )

#         return True

#     def to_diagraph(self, filename=None):
#         """Return a graphviz instance of a diagraph from workflow."""
#         if filename is None:
#             filename = self.id
#         f = Digraph(self.name, filename='{}.gv'.format(filename))

#         for task in self.flow.tasks:
#             if task.dependencies is not None:
#                 for dep in task.dependencies:
#                     f.edge(dep, task.name)

#         return f

#     def fetch_workflow_values(self, input_string):
#         """Get referenced template value from workflow level value.

#         This method returns a dictionary where the keys are the workflow variables in
#         input_string and values are the fetched values from workflow.
#         """
#         references = parse_double_quote_workflow_vars(input_string)

#         if not references:
#             return {}
#         values = {}
#         for ref in references:
#             # validate formatting
#             qbvar.validate_ref_variable_format(ref)
#             try:
#                 _, attr, prop, name = ref.split('.')
#             except ValueError:
#                 *_, name = ref.split('.')
#                 if name == 'id':
#                     values[ref] = self.id
#                 elif name == 'name':
#                     values[ref] = self.name
#             else:
#                 if attr in ('inputs', 'outputs'):
#                     if prop == 'parameters':
#                         values[ref] = self.inputs.get_parameter_value(name)
#                     elif prop == 'artifacts':
#                         values[ref] = self.inputs.get_artifact_value(name)
#                 elif attr == 'operators':
#                     assert name == 'image', \
#                         'The only valid value for workflow.operators is image name.'
#                     values[ref] = self.get_operator(prop).image
#                 else:
#                     raise ValueError(
#                         f'Invalid workflow variable: {ref}. '
#                         f'Variable type must be "parameters", "artifacts" '
#                         f'or "operators" not "{attr}"'
#                     )

#         return values

#     def update_inputs_values(self, values):
#         """Update workflow inputs values from a dictionary.

#         The dictionary should have two keys for ``parameters`` and ``artifacts``.
#         The values for each key is a dictionary where the key is the name of the
#         target variable and value is ``key: value`` that should be updated.

#         For instance this input updates the value for workers to 6 and grid-name to
#         classroom.

#         .. code-block:: python

#             {
#                 'parameters': {
#                     'worker': {'value': 6},
#                     'grid-name': {'value': 'classroom'}
#                 }
#             }

#         """
#         if not self.inputs:
#             raise ValueError(f'Workflow "{self.name}" has no inputs.')

#         if values.get('parameters') is not None:
#             for k, v in values['parameters'].items():
#                 self.inputs.set_parameter_value(k, v)

#         if values.get('artifacts') is not None:
#             for k, v in values['artifacts'].items():
#                 self.inputs.set_artifact_value(k, v)

#         if values.get('user_data') is not None:
#             user_data = self.inputs.user_data

#             if user_data is None:
#                 user_data = {}

#             user_data.update(values['user_data'])

#             self.inputs.user_data = user_data

#     def hydrate_workflow_templates(self, inputs: WorkflowInputs = None):
#         """Find and replace {{workflow.x.y.z}} variables with input values.

#         This method returns the workflow as a dictionary with {{workflow.x.y.z}}
#         variables replaced by workflow input values.
#         """

#         if inputs is None:
#             inputs = WorkflowInputs()

#         self.update_inputs_values(inputs.dict())

#         return hydrate_templates(self, wf_value=self.dict(exclude_unset=True))

#     @property
#     def nodes_links(self):
#         """Get nodes and links for workflow visualization."""
#         task_names = [task.name for task in self.flow.tasks]
#         nodes = [{'name': name} for name in task_names]
#         links = []
#         for count, task in enumerate(self.flow.tasks):
#             for source in task.dependencies:
#                 links.append(
#                     {'source': task_names.index(source), 'target': count})

#         return {'nodes': nodes, 'links': links}

#     @property
#     def artifacts(self):
#         """List of workflow artifacts."""
#         artifacts = []
#         # collect all artifacts
#         for template in self.templates:
#             artifacts.extend(template.artifacts)

#         for task in self.flow.tasks:
#             args = task.arguments
#             if not args:
#                 continue
#             if not args.artifacts:
#                 continue
#             artifacts.extend(args.artifacts)

#         if self.inputs and self.inputs.artifacts:
#             artifacts.extend(self.inputs.artifacts)

#         if self.outputs and self.outputs.artifacts:
#             artifacts.extend(self.outputs.artifacts)

#         return artifacts

#     def get_operator(self, name):
#         """Get operator by name."""
#         operator = [op for op in self.operators if op.name == name]
#         if not operator:
#             raise ValueError(f'Invalid operator name: {name}')
#         return operator[0]

#     def get_inputs_parameter(self, name):
#         """Get an inputs parameter by name."""
#         if self.inputs:
#             return self.inputs.get_parameter(name)
#         else:
#             raise ValueError('Workflow has no inputs.')

#     def get_inputs_artifact(self, name):
#         """Get an inputs artifact by name."""
#         if self.inputs:
#             return self.inputs.get_artifact(name)
#         else:
#             raise ValueError('Workflow has no inputs.')

#     def get_outputs_parameter(self, name):
#         """Get an outpus parameter by name."""
#         if self.outputs:
#             return self.outputs.get_parameter(name)
#         else:
#             raise ValueError('Workflow has no outputs.')

#     def get_outputs_artifact(self, name):
#         """Get an outputs artifact by name."""
#         if self.outputs:
#             return self.outputs.get_artifact(name)
#         else:
#             raise ValueError('Workflow has no outputs.')

#     def get_template(self, name):
#         """Get template by name."""
#         if self.templates:
#             template = [t for t in self.templates if t.name == name]
#             if not template:
#                 raise ValueError(f'No template with name: {name}.')
#         else:
#             raise ValueError(f'Workflow {self.name} has no templates.')

#         return template[0]

#     def get_task(self, name):
#         """Get a task from the flow by name."""
#         task = [t for t in self.flow.tasks if t.name == name]
#         if not task:
#             raise ValueError('No task with name: {name}')
#         return task[0]


# def hydrate_templates(workflow, wf_value=None):
#     """Replace all ``{{ workflow.x.y.z }}`` variables with corresponding values.

#     Cycle through an arbitrary workflow value (dictionary, list, string etc...)
#     and hydrate any workflow template value with it's actual value. This function
#     should mostly be used by the plugin libraries when converting a queenbee
#     workflow to their own job scheduling language. As such the workflow should
#     contain all the required variable values indicated by a ``{{ workflow.x.y...z }}``.

#     In most cases you should use Workflow's ``hydrate_workflow_templates`` method instead
#     of using this function directly.
#     """
#     if isinstance(wf_value, list):
#         wf_value = [hydrate_templates(workflow, item) for item in wf_value]

#     elif isinstance(wf_value, str):
#         values = workflow.fetch_workflow_values(wf_value)

#         if values == {}:
#             pass

#         elif len(values.keys()) == 1:
#             for match_k, match_v in values.items():
#                 assert match_v is not None, \
#                     "{{%s}} cannot reference an empty or null value." % (
#                         match_k)

#                 pattern = r"^\s*{{\s*" + match_k + r"\s*}}\s*$"

#                 # if match is not None then it means that the string value
#                 # "{{ workflow.key }}" does not require string replace values like the
#                 # following example: "{{ workflow.id }}-{{ workflow.name }}"
#                 match = re.search(pattern, wf_value)

#                 if isinstance(match_v, list) or isinstance(match_v, dict) or \
#                         match is not None:
#                     wf_value = match_v
#                 else:
#                     wf_value = replace_double_quote_vars(
#                         wf_value, match_k, str(match_v)
#                         )

#         else:
#             new_v = wf_value
#             for match_k, match_v in values.items():
#                 assert not isinstance(match_v, list) or not isinstance(match_v, dict), \
#                     "Cannot concat {{%s}} of type %s into %s" % (
#                         match_k, type(match_v), wf_value)
#                 new_v = replace_double_quote_vars(new_v, match_k, str(match_v))

#             wf_value = new_v

#     elif isinstance(wf_value, dict):
#         for k, v in wf_value.items():
#             wf_value[k] = hydrate_templates(workflow, v)

#     return wf_value


# # required for self.referencing model
# # see https://pydantic-docs.helpmanual.io/#self-referencing-models
# Workflow.update_forward_refs()
