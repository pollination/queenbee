"""Queenbee recipe class.

Recipe is a collection of operators and inter-related tasks that describes an end to
end steps for the recipe.
"""
import os
import shutil
import json
from typing import List, Union

import yaml
from pydantic import Field, validator, root_validator


from ..base.basemodel import BaseModel
from ..operator import Operator
from ..operator.function import Function
from ..operator.operator import Config

from .dag import DAG, DAGInputs
from .metadata import MetaData
from .dependency import Dependency, DependencyType


class TemplateFunction(Function):
    """Function template."""

    config: Config = Field(
        ...,
        description='The operator config to use for this function'
    )

    @classmethod
    def from_operator(cls, operator: Operator) -> list:
        """Generate a list of template functions from an operator

        Arguments:
            operator {Operator} -- An Operator

        Returns:
            list -- A list of template functions
        """
        functions = []

        for function in operator.functions:
            input_dict = function.to_dict()
            input_dict['name'] = f'{operator.__hash__}/{function.name}'
            input_dict['config'] = operator.config.to_dict()
            functions.append(cls.parse_obj(input_dict))

        return functions


class Recipe(BaseModel):
    """A Queenbee Recipe"""

    metadata: MetaData = Field(
        None,
        description='Recipe metadata information.'
    )

    dependencies: List[Dependency] = Field(
        None,
        description='A list of operators and other recipes this recipe depends on.'
    )

    flow: List[DAG] = Field(
        ...,
        description='A list of tasks to create a DAG recipe.'
    )

    @classmethod
    def from_folder(cls, folder_path: str):
        """Generate a recipe from a folder

        Note:
            Here is an example of a Recipe folder:
            ::

                .
                ├── .dependencies
                │   ├── operators
                │   │   └── <sha-256>.yaml
                │   └── recipes
                │       └── <sha-256>.yaml
                ├── flow
                |   ├── sub-dag.yaml
                │   └── main.yaml
                ├── dependencies.yaml
                └── recipe.yaml

        Arguments:
            folder_path {str} -- Path to the folder

        Returns:
            Recipe -- A Recipe
        """
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
        """Check the `main` DAG exists in the flow"""
        for dag in v:
            if dag.name == 'main':
                return v
            elif dag.name.split('/')[-1] == 'main':
                return v

        raise ValueError('No DAG with name "main" found in flow')

    @validator('flow')
    def sort_list(cls, v):
        """Sort the list of DAGs by name"""
        v.sort(key=lambda x: x.name)
        return v

    @validator('flow')
    def check_dag_names(cls, v, values):
        """Check DAG names do not overlap with dependency names"""
        op_names = [dep.ref_name for dep in values.get('dependencies')]

        for dag in v:
            assert dag.name not in op_names, \
                ValueError(
                    f'DAG name {dag.name} cannot be used because a recipe dependency'
                    f' already uses it'
                )

        return v

    @validator('flow')
    def check_template_dependency_names(cls, v, values):
        """Check all DAG template names exist in dependencies or other DAGs"""
        op_names = [dep.ref_name for dep in values.get('dependencies')]
        op_names.extend([dag.name for dag in v])

        for dag in v:
            for template in dag.templates:
                operator = template.split('/')[0]
                assert operator in op_names, \
                    ValueError(
                        f'Cannot use template {template} from DAG {dag.name} because no'
                        f' dependency or other DAG matching that name was found.'
                    )

        return v

    @property
    def inputs(self) -> DAGInputs:
        """Get the Recipe's inputs

        Returns:
            DAGInputs -- The inputs of the entrypoint DAG
        """
        return self.flow.root_dag.inputs

    @property
    def is_locked(self) -> bool:
        """Indicates whether the Recipe dependencies are all locked

        Returns:
            bool -- True if all dependencies are locked
        """
        return all(map(lambda x: x.is_locked, self.dependencies))

    @staticmethod
    def dependency_by_name(dependencies: List[Dependency], name: str) -> Dependency:
        """Retrieve a dependency by its reference name (name or alias)

        Arguments:
            dependencies {List[Dependency]} -- A list of dependencies
            name {str} -- The name or alias to search dependencies by

        Raises:
            ValueError: No dependency found with the input name

        Returns:
            Dependency -- A dependency
        """
        res = next(filter(lambda x: x.ref_name == name, dependencies), None)

        if res is None:
            raise ValueError(f'No dependency with reference name {name} found')

        return res

    @staticmethod
    def dag_by_name(flow: List[DAG], name: str) -> DAG:
        """Retrieve a DAG from a list by its name

        Arguments:
            flow {List[DAG]} -- A list of DAGs
            name {str} -- The name to search by

        Raises:
            ValueError: No DAG found with the input name

        Returns:
            DAG -- A DAG
        """
        res = next(filter(lambda x: x.name == name, flow), None)

        if res is None:
            raise ValueError(f'No DAG with reference name {name} found in flow')

        return res

    def lock_dependencies(self):
        """Lock the dependencies by fetching them and storing their digest"""
        for dependency in self.dependencies:
            dependency.fetch()

    def write_dependency_file(self, folder_path: str):
        """Write the locked dependencies to a Recipe folder

        Arguments:
            folder_path {str} -- The path to the recipe folder
        """

        self_dict = json.loads(self.json(by_alias=True, exclude_unset=True))

        with open(os.path.join(folder_path, 'dependencies.yaml'), 'w') as f:
            f.write(
                yaml.dump(
                    {'dependencies': self_dict['dependencies']},
                    default_flow_style=False
                )
            )

    def to_folder(self, folder_path: str):
        """Write a Recipe to a folder

        Note:
            Here is an example of a Recipe folder:
            ::

                .
                ├── .dependencies
                │   ├── operators
                │   │   └── <sha-256>.yaml
                │   └── recipes
                │       └── <sha-256>.yaml
                ├── flow
                |   ├── sub-dag.yaml
                │   └── main.yaml
                ├── dependencies.yaml
                └── recipe.yaml

        Arguments:
            folder_path {str} -- The path to the Recipe folder
        """

        os.mkdir(os.path.join(folder_path, 'flow'))

        self.metadata.to_yaml(
            os.path.join(folder_path, 'recipe.yaml'), exclude_unset=True
        )

        self.write_dependency_file(folder_path)

        for dag in self.flow:
            dag.to_yaml(
                os.path.join(folder_path, 'flow', f'{dag.name}.yaml'),
                exclude_unset=True
            )

    def write_dependencies(self, folder_path: str):
        """Fetch dependencies manifests and write them to the `.dependencies` folder

        Arguments:
            folder_path {str} -- Path to the recipe folder
        """
        dependencies_folder = os.path.join(folder_path, '.dependencies')
        operator_folder = os.path.join(dependencies_folder, 'operators')
        recipes_folder = os.path.join(dependencies_folder, 'recipes')

        if not os.path.isdir(dependencies_folder):
            os.mkdir(dependencies_folder)

        if not os.path.isdir(operator_folder):
            os.mkdir(operator_folder)

        if not os.path.isdir(recipes_folder):
            os.mkdir(recipes_folder)

        for dependency in self.dependencies:
            if dependency.type == DependencyType.operator:
                raw_dep, digest = dependency.fetch()
                dep = Operator.parse_raw(raw_dep)
                dep.to_yaml(
                    os.path.join(
                        folder_path, '.dependencies', 'operators', f'{digest}.yaml'
                    )
                )

            elif dependency.type == DependencyType.recipe:
                raw_dep, digest = dependency.fetch()
                dep = self.__class__.parse_raw(raw_dep)
                dep.write_dependencies(folder_path)
                dep.to_yaml(
                    os.path.join(
                        folder_path, '.dependencies', 'recipes', f'{digest}.yaml'
                    )
                )


class BakedRecipe(Recipe):
    """Baked Recipe.

    A Baked Recipe contains all the templates referred to in the DAG within a templates
    list.
    """

    digest: str

    # templates only exist in the compiled version of a recipe
    templates: List[Union[TemplateFunction, DAG]] = Field(
        ...,
        description='A list of templates. Templates can be Function or a DAG.'
    )

    @classmethod
    def from_recipe(cls, recipe: Recipe):
        """Bake a recipe

        Arguments:
            recipe {Recipe} -- A Queenbee recipe

        Raises:
            ValueError: The dependencies or templates do not match the flow

        Returns:
            BakedRecipe -- A baked recipe
        """

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
        )

        input_dict = recipe.to_dict()
        input_dict['digest'] = digest
        input_dict['flow'] = [dag.to_dict() for dag in flow]
        input_dict['templates'] = [template.to_dict() for template in templates]

        return cls.parse_obj(input_dict)

    @classmethod
    def from_folder(cls, folder_path: str, refresh_deps: bool = True):
        """Generate a baked recipe from a recipe folder

        Note:
            Here is an example of a Recipe folder:
            ::

                .
                ├── .dependencies
                │   ├── operators
                │   │   └── <sha-256>.yaml
                │   └── recipes
                │       └── <sha-256>.yaml
                ├── flow
                |   ├── sub-dag.yaml
                │   └── main.yaml
                ├── dependencies.yaml
                └── recipe.yaml


        Arguments:
            folder_path {str} -- The path to the folder to read

        Keyword Arguments:
            refresh_deps {bool} -- Fetch the dependencies from their source instead of
                the ``.dependencies`` folder (default: {True})

        Returns:
            BakedRecipe -- A baked recipe
        """
        dependencies_folder = os.path.join(folder_path, '.dependencies')

        recipe = Recipe.from_folder(folder_path)

        digest = recipe.__hash__

        if refresh_deps:
            if os.path.exists(dependencies_folder) and \
                    os.path.isdir(dependencies_folder):
                shutil.rmtree(dependencies_folder)
            recipe.write_dependencies(folder_path)

        templates = []

        for operator_path in os.listdir(os.path.join(dependencies_folder, 'operators')):
            operator = Operator.from_file(
                os.path.join(dependencies_folder, 'operators', operator_path)
            )
            templates.extend(TemplateFunction.from_operator(operator))

        for sub_recipe_path in os.listdir(os.path.join(dependencies_folder, 'recipes')):
            sub_recipe = Recipe.from_file(
                os.path.join(dependencies_folder, 'recipes', sub_recipe_path)
            )
            sub_baked_recipe = cls.from_recipe(sub_recipe)
            templates.extend(sub_baked_recipe.templates)
            templates.extend(sub_baked_recipe.flow)

        flow = cls.replace_template_refs(
            dependencies=recipe.dependencies,
            dags=recipe.flow,
            digest=digest,
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
    ) -> List[DAG]:
        """Replace DAG Task template names with unique dependency digest based names

        Arguments:
            dependencies {List[Dependency]} -- A list of locked dependencies
            dags {List[DAG]} -- A list of DAGs
            digest {str} -- The digest of the Recipe used to create the Baked Recipe

        Raises:
            ValueError: Unresolvable dependency in a task

        Returns:
            List[DAG] -- A list of DAGs with updated template names
        """
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
                    continue

                dep = cls.dependency_by_name(dependencies, template_dep_list[0])

                # Template name is another Recipe
                if dep.type == DependencyType.recipe:
                    assert len(template_dep_list) == 1, \
                        ValueError(
                            f'Unresolvable Recipe template dependency {task.template}'
                        )
                    template_dep = f'{dep.digest}/main'

                # Template name is an Operator Function
                elif dep.type == DependencyType.operator:
                    assert len(template_dep_list) == 2, \
                        ValueError(
                            f'Unresolvable Operator function template dependency'
                            f' {task.template}'
                        )
                    template_dep = f'{dep.digest}/{template_dep_list[1]}'

                task.template = template_dep

        return dags

    @validator('flow')
    def check_template_dependency_names(cls, v, values):
        """Overwrite test function from inherited class"""
        return v

    @validator('templates')
    def remove_duplicates(cls, v):
        """Remove duplicated templates by name"""
        temp_names = []
        templates = []
        for template in v:
            if template.name not in temp_names:
                temp_names.append(template.name)
                templates.append(template)

        return templates

    @root_validator
    def check_inputs(cls, values):
        """Check DAG Task inputs match template inputs"""
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
        """Retrieve a template from a list by name

        Arguments:
            templates {List[Union[DAG, TemplateFunction]]} -- A list of templates
            name {str} -- The name to retrieve a template byt

        Raises:
            ValueError: Template not found

        Returns:
            Union[DAG, TemplateFunction] -- A template
        """

        res = next(filter(lambda x: x.name == name, templates), None)

        if res is None:
            raise ValueError(f'No dependency with reference name {name} found')

        return res
