"""Queenbee workflow class.

Workflow is a collection of operators and inter-related tasks that describes an end to
end steps for the workflow.
"""
from queenbee.schema.qutil import BaseModel
from pydantic import Schema, validator
from typing import List, Union
from enum import Enum
from uuid import UUID, uuid4
import json
import os
from queenbee.schema.dag import DAG
from queenbee.schema.arguments import Arguments
from queenbee.schema.operator import Operator
from queenbee.schema.function import Function


class Workflow(BaseModel):
    """A DAG Workflow."""
    type: Enum('Workflow', {'type': 'Workflow'}) = 'Workflow'

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


# required for self.referencing model
# see https://pydantic-docs.helpmanual.io/#self-referencing-models
Workflow.update_forward_refs()
