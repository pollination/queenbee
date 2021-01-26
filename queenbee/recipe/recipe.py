"""Queenbee recipe class.

Recipe is a collection of plugins and inter-related tasks that describes an end to
end steps for the recipe.
"""
import os
import shutil
import json
from typing import List, Union, Dict

import yaml
from pydantic import Field, validator, root_validator, constr

from ..base.basemodel import BaseModel
from ..base.metadata import MetaData

from ..config import Config
from ..plugin import Plugin
from ..plugin.function import Function
from ..plugin.plugin import PluginConfig

from .dag import DAG, DAGInputs, DAGOutputs
from .dependency import Dependency, DependencyKind


class TemplateFunction(Function):
    """Function template."""
    type: constr(regex='^TemplateFunction$') = 'TemplateFunction'

    config: PluginConfig = Field(
        ...,
        description='The plugin config to use for this function'
    )

    @classmethod
    def from_plugin(cls, plugin: Plugin) -> list:
        """Generate a list of template functions from a plugin

        Arguments:
            plugin {Plugin} -- A plugin

        Returns:
            list -- A list of template functions
        """
        functions = []

        for function in plugin.functions:
            input_dict = function.to_dict()
            input_dict['type'] = 'TemplateFunction'
            input_dict['name'] = f'{plugin.__hash__}/{function.name}'
            input_dict['config'] = plugin.config.to_dict()
            functions.append(cls.parse_obj(input_dict))

        return functions


class Recipe(BaseModel):
    """A Queenbee Recipe"""
    api_version: constr(regex='^v1beta1$') = Field('v1beta1', readOnly=True)

    type: constr(regex='^Recipe$') = 'Recipe'

    metadata: MetaData = Field(
        None,
        description='Recipe metadata information.'
    )

    dependencies: List[Dependency] = Field(
        None,
        description='A list of plugins and other recipes this recipe depends on.'
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
                │   ├── plugins
                │   │   └── <sha-256>.yaml
                │   └── recipes
                │       └── <sha-256>.yaml
                ├── flow
                |   ├── sub-dag.yaml
                │   └── main.yaml
                ├── dependencies.yaml
                └── package.yaml

        Arguments:
            folder_path {str} -- Path to the folder

        Returns:
            Recipe -- A Recipe
        """
        folder_path = os.path.realpath(folder_path)
        meta_path = os.path.join(folder_path, 'package.yaml')
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

    @validator('flow', allow_reuse=True)
    def check_entrypoint(cls, v):
        """Check the `main` DAG exists in the flow"""
        for dag in v:
            if dag.name == 'main':
                return v
            elif dag.name.split('/')[-1] == 'main':
                return v

        raise ValueError('No DAG with name "main" found in flow')

    @validator('flow', allow_reuse=True)
    def sort_list(cls, v):
        """Sort the list of DAGs by name"""
        v.sort(key=lambda x: x.name)
        return v

    @validator('flow', allow_reuse=True)
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

    @validator('flow', allow_reuse=True)
    def check_template_dependency_names(cls, v, values):
        """Check all DAG template names exist in dependencies or other DAGs"""
        op_names = [dep.ref_name for dep in values.get('dependencies')]
        op_names.extend([dag.name for dag in v])

        for dag in v:
            for template in dag.templates:
                plugin = template.split('/')[0]
                assert plugin in op_names, \
                    ValueError(
                        f'Cannot use template {template} from DAG {dag.name} because no'
                        f' dependency or other DAG matching that name was found.'
                    )

        return v

    @property
    def root_dag(self) -> DAG:
        return self.dag_by_name(flow=self.flow, name='main')

    @property
    def inputs(self) -> List[DAGInputs]:
        """Get the Recipe's inputs

        Returns:
            List[DAGInputs] -- The inputs of the entrypoint DAG
        """
        return self.root_dag.inputs

    @property
    def outputs(self) -> List[DAGOutputs]:
        """Get the Recipe's outputs

        Returns:
            List[DAGOutputs] -- The outputs of the entrypoint DAG
        """
        return self.root_dag.outputs

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
            raise ValueError(
                f'No DAG with reference name {name} found in flow')

        return res

    def lock_dependencies(self, config: Config = Config()):
        """Lock the dependencies by fetching them and storing their digest"""
        for dependency in self.dependencies:
            auth_header = config.get_auth_header(
                repository_url=dependency.source)
            dependency.fetch(auth_header=auth_header)

    def write_dependency_file(self, folder_path: str):
        """Write the locked dependencies to a Recipe folder

        Arguments:
            folder_path {str} -- The path to the recipe folder
        """

        self_dict = json.loads(self.json(by_alias=True, exclude_unset=False))

        with open(os.path.join(folder_path, 'dependencies.yaml'), 'w') as f:
            f.write(
                yaml.dump(
                    {'dependencies': self_dict['dependencies']},
                    default_flow_style=False
                )
            )

    def to_folder(self, folder_path: str, readme_string: str = None):
        """Write a Recipe to a folder

        Note:
            Here is an example of a Recipe folder:
            ::

                .
                ├── .dependencies
                │   ├── plugin
                │   │   └── plugin-dep-name
                │   │       ├── functions
                │   │       │   ├── func-1.yaml
                │   │       │   ├── ...
                │   │       │   └── func-n.yaml
                │   │       ├── config.yaml
                │   │       └── package.yaml
                │   └── recipe
                │       └── recipe-dep-name
                │           ├── .dependencies
                │           │   ├── plugin
                │           │   └── recipe
                │           ├── flow
                │           │   └── main.yaml
                │           ├── dependencies.yaml
                │           └── package.yaml
                ├── flow
                │   └── main.yaml
                ├── dependencies.yaml
                └── package.yaml

        Arguments:
            folder_path {str} -- The path to the Recipe folder

        Keyword Arguments:
            readme_string {str} -- The README file string (default: {None})
        """

        os.makedirs(os.path.join(folder_path, 'flow'), exist_ok=True)

        self.metadata.to_yaml(
            os.path.join(folder_path, 'package.yaml'), exclude_unset=False
        )

        self.write_dependency_file(folder_path)

        for dag in self.flow:
            dag.to_yaml(
                os.path.join(folder_path, 'flow', f'{dag.name}.yaml'),
                exclude_unset=False
            )

        if readme_string is not None:
            with open(os.path.join(folder_path, 'README.md'), 'w') as f:
                f.write(readme_string)

        with open(os.path.join(folder_path, 'LICENSE'), 'w') as f:
            f.write('To see the license for this package refer to package.yaml')

    def write_dependencies(self, folder_path: str, config: Config = Config()):
        """Fetch dependencies manifests and write them to the `.dependencies` folder

        Arguments:
            folder_path {str} -- Path to the recipe folder
        Keyword Arguments:
            config {Config} -- A queenbee config object (default: {Config()})
        """
        dependencies_folder = os.path.join(folder_path, '.dependencies')
        plugin_folder = os.path.join(dependencies_folder, 'plugin')
        recipes_folder = os.path.join(dependencies_folder, 'recipe')

        if not os.path.isdir(dependencies_folder):
            os.makedirs(dependencies_folder, exist_ok=True)

        if not os.path.isdir(plugin_folder):
            os.makedirs(plugin_folder, exist_ok=True)

        if not os.path.isdir(recipes_folder):
            os.makedirs(recipes_folder, exist_ok=True)

        for dependency in self.dependencies:
            auth_header = config.get_auth_header(
                repository_url=dependency.source)
            package_version = dependency.fetch(auth_header=auth_header)
            dep = package_version.manifest

            if dependency.kind == DependencyKind.recipe:
                dep.write_dependencies(
                    folder_path=os.path.join(
                        recipes_folder, dependency.ref_name),
                    config=config,
                )

            dep.to_folder(
                folder_path=os.path.join(
                    folder_path, '.dependencies',
                    dependency.dependency_kind, dependency.ref_name),
                readme_string=package_version.readme
            )


class BakedRecipe(Recipe):
    """Baked Recipe.

    A Baked Recipe contains all the templates referred to in the DAG within a templates
    list.
    """
    type: constr(regex='^BakedRecipe$') = 'BakedRecipe'

    digest: str

    # templates only exist in the compiled version of a recipe
    templates: List[Union[TemplateFunction, DAG]] = Field(
        ...,
        description='A list of templates. Templates can be Function or a DAG.'
    )

    @classmethod
    def from_recipe(cls, recipe: Recipe, config: Config = Config()):
        """Bake a recipe

        Arguments:
            recipe {Recipe} -- A Queenbee recipe

        Keyword Arguments:
            config {Config} -- A queenbee config object (default: {Config()})

        Raises:
            ValueError: The dependencies or templates do not match the flow

        Returns:
            BakedRecipe -- A baked recipe
        """

        recipe = recipe.copy(deep=True)

        digest = recipe.__hash__

        digest_dict = {
            '__self__': digest
        }

        templates = []

        for dependency in recipe.dependencies:
            auth_header = config.get_auth_header(
                repository_url=dependency.source)
            package_version = dependency.fetch(auth_header=auth_header)
            dep = package_version.manifest

            if dependency.kind == DependencyKind.recipe:
                sub_recipe = cls.from_recipe(recipe=dep, config=config)

                templates.extend(sub_recipe.templates)
                templates.extend(sub_recipe.flow)
                digest_dict[dependency.ref_name] = sub_recipe.digest

            elif dependency.kind == DependencyKind.plugin:
                templates.extend(TemplateFunction.from_plugin(dep))
                digest_dict[dependency.ref_name] = dep.__hash__

            else:
                raise ValueError(
                    f'Dependency of type {dependency.kind} not recognized')

        flow = cls.replace_template_refs(
            dependencies=recipe.dependencies,
            dags=recipe.flow,
            digest_dict=digest_dict,
        )

        input_dict = recipe.to_dict()
        input_dict['type'] = 'BakedRecipe'
        input_dict['digest'] = digest
        input_dict['flow'] = [dag.to_dict() for dag in flow]
        input_dict['templates'] = [template.to_dict()
                                   for template in templates]

        return cls.parse_obj(input_dict)

    @classmethod
    def from_folder(cls, folder_path: str, refresh_deps: bool = True, config: Config = Config()):
        """Generate a baked recipe from a recipe folder

        Note:
            Here is an example of a Recipe folder:
            ::

                .
                ├── .dependencies
                │   ├── plugins
                │   │   └── <sha-256>.yaml
                │   └── recipes
                │       └── <sha-256>.yaml
                ├── flow
                |   ├── sub-dag.yaml
                │   └── main.yaml
                ├── dependencies.yaml
                └── package.yaml


        Arguments:
            folder_path {str} -- The path to the folder to read

        Keyword Arguments:
            refresh_deps {bool} -- Fetch the dependencies from their source instead of
                the ``.dependencies`` folder (default: {True})
            config {Config} -- A queenbee config object (default: {Config()})

        Returns:
            BakedRecipe -- A baked recipe
        """
        dependencies_folder = os.path.join(folder_path, '.dependencies')

        recipe = Recipe.from_folder(folder_path)

        digest = recipe.__hash__

        digest_dict = {
            '__self__': digest
        }

        if refresh_deps:
            if os.path.exists(dependencies_folder) and \
                    os.path.isdir(dependencies_folder):
                shutil.rmtree(dependencies_folder)
            recipe.write_dependencies(
                folder_path=folder_path,
                config=config,
            )

        templates = []

        plugins_folder = os.path.join(dependencies_folder, 'plugin')
        if os.path.isdir(plugins_folder):
            for plugin_dep_name in os.listdir(plugins_folder):
                plugin = Plugin.from_folder(
                    folder_path=os.path.join(
                        dependencies_folder, 'plugin', plugin_dep_name
                    )
                )
                templates.extend(TemplateFunction.from_plugin(plugin))
                digest_dict[plugin_dep_name] = plugin.__hash__

        recipes_folder = os.path.join(dependencies_folder, 'recipe')
        if os.path.isdir(recipes_folder):
            for recipe_dep_name in os.listdir(recipes_folder):
                sub_baked_recipe = cls.from_folder(
                    folder_path=os.path.join(
                        dependencies_folder, 'recipe', recipe_dep_name
                    ),
                    refresh_deps=refresh_deps,
                    config=config,
                )

                templates.extend(sub_baked_recipe.templates)
                templates.extend(sub_baked_recipe.flow)
                digest_dict[recipe_dep_name] = sub_baked_recipe.digest

        flow = cls.replace_template_refs(
            dependencies=recipe.dependencies,
            dags=recipe.flow,
            digest_dict=digest_dict,
        )

        input_dict = recipe.to_dict()
        input_dict['type'] = 'BakedRecipe'
        input_dict['digest'] = digest
        input_dict['flow'] = [dag.to_dict() for dag in flow]
        input_dict['templates'] = [template.to_dict()
                                   for template in templates]

        return cls.parse_obj(input_dict)

    @classmethod
    def replace_template_refs(
        cls,
        dependencies: List[Dependency],
        dags: List[DAG],
        digest_dict: Dict[str, str],
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
            raise ValueError(
                'Cannot resolve template refs without dependencies')

        for dag in dags:
            # Replace name of DAG to "{digest}/{dag.name}"
            dep_hash = digest_dict['__self__']
            dag.name = f'{dep_hash}/{dag.name}'

        for dag in dags:
            for task in dag.tasks:
                template_dep_list = task.template.split('/')

                # Template name is another DAG in the Recipe Flow
                if template_dep_list[0] in dag_names:
                    dep_hash = digest_dict['__self__']
                    task.template = f'{dep_hash}/{template_dep_list[0]}'
                    continue

                dep = cls.dependency_by_name(
                    dependencies, template_dep_list[0])

                try:
                    dep_hash = digest_dict[dep.ref_name]
                except KeyError:
                    raise ValueError(
                        f'Unresolvable dependency name {dep.ref_name}. Did you forget '
                        f'to package or link {dep.ref_name}? '
                        'See `queenbee recipe link --help` for more information.'
                    )

                # Template name is another Recipe
                if dep.kind == DependencyKind.recipe:
                    assert len(template_dep_list) == 1, \
                        ValueError(
                            f'Unresolvable Recipe template dependency {task.template}'
                    )
                    template_dep = f'{dep_hash}/main'

                # Template name is a plugin Function
                elif dep.kind == DependencyKind.plugin:
                    assert len(template_dep_list) == 2, \
                        ValueError(
                            f'Unresolvable Plugin function template dependency'
                            f' {task.template}'
                    )
                    template_dep = f'{dep_hash}/{template_dep_list[1]}'
                else:
                    raise ValueError(f'Invalid dependency type: {dep.kind}')
                task.template = template_dep

        return dags

    @validator('flow', allow_reuse=True)
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

    @property
    def root_dag(self) -> DAG:
        return self.dag_by_name(flow=self.flow, name=f'{self.digest}/main')

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


class RecipeInterface(BaseModel):
    """An interface object for creating a Recipe.

    Recipe information only includes metadata, source, inputs and outputs of a Recipe.
    This object is useful for creating user interface for Recipes.
    """
    api_version: constr(regex='^v1beta1$') = Field('v1beta1', readOnly=True)

    type: constr(regex='^RecipeInterface$') = 'RecipeInterface'

    metadata: MetaData = Field(
        ...,
        description='Recipe metadata information.'
    )

    source: str = Field(
        None,
        description='A URL to the source this recipe from a registry.'
    )

    inputs: List[DAGInputs] = Field(
        None,
        description='A list of recipe inputs.'
    )

    outputs: List[DAGOutputs] = Field(
        None,
        description='A list of recipe outputs.'
    )

    @validator('inputs', 'outputs')
    def create_empty_list(cls, v):
        return [] if not v else v

    @classmethod
    def from_recipe(cls, recipe: Union[Recipe, BakedRecipe], source: str = None):
        """Create a Recipe info from a recipe."""
        return cls(
            metadata=recipe.metadata,
            source=source,
            inputs=recipe.inputs,
            outputs=recipe.outputs
        )
