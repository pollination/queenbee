"""Queenbee workflow class.

Workflow is a collection of operators and inter-related tasks that describes an end to
end steps for the workflow.
"""
import os
import shutil
import json
from typing import List, Union

import yaml
from pydantic import Field, validator, root_validator


from ..base.basemodel import BaseModel
from ..base.io import IOBase
from ..operator import Operator
from ..operator.function import Function
from ..operator.operator import Config

from .dag import DAG
from .metadata import MetaData
from .dependency import Dependency, DependencyType


class TemplateFunction(Function):

    config: Config = Field(
        ...,
        description='The operator config to use for this function'
    )

    @classmethod
    def from_operator(cls, operator: Operator):
        functions = []

        for function in operator.functions:


            input_dict = function.to_dict()
            input_dict['name'] = f'{operator.__hash__}/{function.name}'
            input_dict['config'] = operator.config.to_dict()
            functions.append(cls.parse_obj(input_dict))

        return functions


class Recipe(BaseModel):
    """A DAG Workflow."""

    metadata: MetaData = Field(
        None,
        description='Workflow metadata information.'
    )

    dependencies: List[Dependency] = Field(
        None,
        description='A list of operators and other workflows this workflow depends on.'
    )

    flow: List[DAG] = Field(
        ...,
        description='A list of tasks to create a DAG workflow.'
    )

    @classmethod
    def from_folder(cls, folder_path: str):
        meta_path = os.path.join(folder_path, 'recipe.yaml')
        dependencies_path = os.path.join(folder_path, 'dependencies.yaml')
        flow_path = os.path.join(folder_path, 'flow')
        
        recipe = {}
        
        with open(meta_path, 'r') as f:
            recipe['metadata'] = yaml.load(f, yaml.FullLoader)

        with open(dependencies_path, 'r') as f:
            dependencies = yaml.load(f, yaml.FullLoader)

        recipe.update(dependencies)

        flow = []

        for dag_path in os.listdir(flow_path):

            with open(os.path.join(flow_path, dag_path), 'r') as f:
                flow.append(yaml.load(f, yaml.FullLoader))
      
        recipe['flow'] = flow

        return cls.parse_obj(recipe)

    @validator('flow')
    def check_entrypoint(cls, v):
        for dag in v:
            if dag.name == 'main':
                return v
            elif dag.name.split('/')[-1] == 'main':
                return v

        raise ValueError('No DAG with name "main" found in flow')    

    @validator('flow')
    def sort_list(cls, v):
        v.sort(key=lambda x: x.name)
        return v

    @property
    def inputs(self):
        return self.flow.root_dag.inputs

    @property
    def is_locked(self):
        return all(map(lambda x: x.is_locked(), self.dependencies))
    
    @staticmethod
    def dependency_by_name(dependencies: List[Dependency], name: str) -> Dependency:
        res = next(filter(lambda x: x.ref_name == name, dependencies), None)

        if res is None:
            raise ValueError(f'No dependency with reference name {name} found')

        return res


    @staticmethod
    def dag_by_name(flow: List[DAG], name: str) -> DAG:
        res = next(filter(lambda x: x.name == name, flow), None)

        if res is None:
            raise ValueError(f'No DAG with reference name {name} found in flow')

        return res
    
    def lock_dependencies(self):

        for dependency in self.dependencies:
            dependency.fetch()

    def write_dependency_lock(self, folder_path: str):
        self_dict = json.loads(self.json(by_alias=True, exclude_unset=True))

        with open(os.path.join(folder_path, 'dependencies.yaml'), 'w') as f:
            f.write(yaml.dump({'dependencies': self_dict['dependencies']}, default_flow_style=False))

    def to_folder(self, folder_path: str):

        os.mkdir(os.path.join(folder_path, 'flow'))

        self.metadata.to_yaml(os.path.join(folder_path, 'recipe.yaml'))
        
        self.write_dependency_lock(folder_path)

        for dag in self.flow:
            dag.to_yaml(os.path.join(folder_path, 'flow', f'{dag.name}.yaml'))
        
    def write_dependencies(self, folder_path: str):
        dependencies_folder = os.path.join(folder_path, '.dependencies')
        operator_folder = os.path.join(dependencies_folder, 'operators')
        recipes_folder = os.path.join(dependencies_folder, 'recipes')

        if not os.path.exists(dependencies_folder) or not os.path.isdir(dependencies_folder):
            os.mkdir(dependencies_folder)

        if not os.path.exists(operator_folder) or not os.path.isdir(operator_folder):
            os.mkdir(operator_folder)

        if not os.path.exists(recipes_folder) or not os.path.isdir(recipes_folder):
            os.mkdir(recipes_folder)


        for dependency in self.dependencies:
            if dependency.type == DependencyType.operator:
                raw_dep, digest = dependency.fetch()
                dep = Operator.parse_raw(raw_dep)
                dep.to_yaml(os.path.join(folder_path, '.dependencies', 'operators', f'{digest}.yaml'))

            elif dependency.type == DependencyType.recipe:
                raw_dep, digest = dependency.fetch()
                dep = self.__class__.parse_raw(raw_dep)
                dep.write_dependencies(folder_path)
                dep.to_yaml(os.path.join(folder_path, '.dependencies', 'recipes', f'{digest}.yaml'))




# This class is used for validation purposes
class BakedRecipe(Recipe):

    digest: str

    # templates only exist in the compiled version of a workflow
    templates: List[Union[TemplateFunction, DAG]] = Field(
        ...,
        description='A list of templates. Templates can be Function or a DAG.'
    )


    @classmethod
    def from_recipe(cls, recipe: Recipe):

        recipe = recipe.copy(deep=True)

        digest = recipe.__hash__

        templates = []

        for dependency in recipe.dependencies:
            dep_bytes, dep_hash = dependency.fetch()

            if dependency.type == 'recipe':
                dep = Recipe.parse_raw(dep_bytes)
                sub_recipe = cls.from_recipe(dep)

                templates.extend(sub_recipe.templates)
                templates.extend(sub_recipe.flow)


            elif dependency.type == 'operator':
                dep = Operator.parse_raw(dep_bytes)
                templates.extend(TemplateFunction.from_operator(dep))

            else:
                raise ValueError(f'Dependency of type {dependency.type} not recognized')

        flow = cls.replace_template_refs(
            dependencies=recipe.dependencies,
            dags=recipe.flow,
            digest=digest,
            # templates=templates,
        )

        input_dict = recipe.to_dict()
        input_dict['digest'] = digest
        input_dict['flow'] = [dag.to_dict() for dag in flow]
        input_dict['templates'] = [template.to_dict() for template in templates]

        return cls.parse_obj(input_dict)


    @classmethod
    def from_folder(cls, folder_path: str, refresh_deps: bool = True):
        
        dependencies_folder = os.path.join(folder_path, '.dependencies')

        recipe = Recipe.from_folder(folder_path)
        
        digest = recipe.__hash__
        
        if refresh_deps:
            if os.path.exists(dependencies_folder) and os.path.isdir(dependencies_folder):
                shutil.rmtree(dependencies_folder)
            recipe.write_dependencies(folder_path)

        templates = []

        for operator_path in os.listdir(os.path.join(dependencies_folder, 'operators')):
            operator = Operator.from_file(os.path.join(dependencies_folder, 'operators', operator_path))
            templates.extend(TemplateFunction.from_operator(operator))

        for sub_recipe_path in os.listdir(os.path.join(dependencies_folder, 'recipes')):
            sub_recipe = Recipe.from_file(os.path.join(dependencies_folder, 'recipes', sub_recipe_path))
            sub_baked_recipe = cls.from_recipe(sub_recipe)
            templates.extend(sub_baked_recipe.templates)
            templates.extend(sub_baked_recipe.flow)

        flow = cls.replace_template_refs(
            dependencies=recipe.dependencies,
            dags=recipe.flow,
            digest=digest,
            # templates=templates,
        )

        input_dict = recipe.to_dict()
        input_dict['digest'] = digest
        input_dict['flow'] = [dag.to_dict() for dag in flow]
        input_dict['templates'] = [template.to_dict() for template in templates]

        return cls.parse_obj(input_dict)


    @classmethod
    def replace_template_refs(
        cls,
        dependencies: List[Dependency],
        dags: List[DAG],
        digest: str,
        # templates: List[Union[TemplateFunction, DAG]]
    ):
        dag_names = [dag.name for dag in dags]

        if dependencies is None:
            raise ValueError('Cannot resolve template refs without dependencies')

        for dag in dags:
            # Replace name of DAG to "{digest}/{dag.name}"
            dag.name = f'{digest}/{dag.name}'

        for dag in dags:
            for task in dag.tasks:
                template_dep_list = task.template.split('/')

                # Template name is another DAG in the Recipe Flow
                if template_dep_list[0] in dag_names:
                    task.template = f'{digest}/{template_dep_list[0]}'
                    # template = cls.template_by_name(dags, task.template)
                    # task.check_template(template)
                    continue

                dep = cls.dependency_by_name(dependencies, template_dep_list[0])

                # Template name is another Recipe
                if dep.type == DependencyType.recipe:
                    assert len(template_dep_list) == 1, \
                        ValueError(f'Unresolvable Recipe template dependency {task.template}')
                    template_dep = f'{dep.digest}/main'

                # Template name is an Operator Function
                elif dep.type == DependencyType.operator:
                    assert len(template_dep_list) == 2, \
                        ValueError(f'Unresolvable Operator function template dependency {task.template}')
                    template_dep = f'{dep.digest}/{template_dep_list[1]}'


                task.template = template_dep

                # template = cls.template_by_name(templates, task.template)
                # task.check_template(template)
        return dags


    @validator('templates')
    def remove_duplicates(cls, v):
        temp_names = []
        templates = []
        for template in v:
            if template.name not in temp_names:
                temp_names.append(template.name)
                templates.append(template)

        return templates

    @root_validator
    def check_inputs(cls, values):
        flow = values.get('flow')
        templates = values.get('templates')

        all_templates = templates + flow

        for dag in flow:
            for task in dag.tasks:
                template = cls.template_by_name(all_templates, task.template)
                task.check_template(template)
        
        return values


    @staticmethod
    def template_by_name(templates: List[Union[DAG, TemplateFunction]], name: str) -> Union[DAG, TemplateFunction]:
        res = next(filter(lambda x: x.name == name, templates), None)

        if res is None:
            raise ValueError(f'No dependency with reference name {name} found')

        return res
