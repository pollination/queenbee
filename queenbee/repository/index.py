import os
from typing import List, Union, Dict
from datetime import datetime
from pydantic import Field, validator

from ..base.basemodel import BaseModel
from ..operator.metadata import MetaData as OperatorMetadata
from ..recipe.metadata import MetaData as RecipeMetadata

from ..operator import Operator
from ..recipe import Recipe

from .package import package_resource, resource_from_package, resource_bytes_from_package

class ResourceVersion(BaseModel):

    url: str

    created: datetime

    digest: str

    @classmethod
    def from_resource(cls, resource: Union[Operator, Recipe], package_path: str = None):

        if package_path is None:
            if isinstance(Operator, resource):
                base_url = 'operators'
            elif isinstance(Recipe, resource):
                base_url = 'recipes'
            else:
                raise ValueError(f'resource should be an instance of Operator or Recipe, not: {type(resource)}')

            full_name = f'{resource.metadata.name}-{resource.metadata.version}.tgz'
            package_path = os.path.join(base_url, full_name)

        input_dict = resource.metadata.to_dict()
        input_dict['digest'] = resource.__hash__
        input_dict['created'] = datetime.utcnow()
        input_dict['url'] = package_path

        return cls.parse_obj(input_dict)


class OperatorVersion(ResourceVersion, OperatorMetadata):

    pass


class RecipeVersion(ResourceVersion, RecipeMetadata):

    pass

class RepositoryIndex(BaseModel):
    
    generated: datetime = Field(
        None,
        description='The timestamp at which the index was generated'
    )

    operator: Dict[str, List[OperatorVersion]] = Field(
        {},
        description='A dict of operators accessible by name. Each name key points to a list of operator versions'
    )

    recipe: Dict[str, List[RecipeVersion]] = Field(
        {},
        description='A dict of recipes accessible by name. Each name key points to a list of recipesversions'
    )


    @classmethod
    def from_folder(cls, folder_path):

        index = cls.parse_obj({})
        
        for package in os.listdir(os.path.join(folder_path, 'operators')):
            rel_path = os.path.join('operators', package)
            resource_raw = resource_bytes_from_package(rel_path, folder_path)
            resource = Operator.parse_raw(resource_raw)
            resource_version = OperatorVersion.from_resource(resource, rel_path)
            index.index_operator_version(resource_version)

        for package in os.listdir(os.path.join(folder_path, 'recipes')):
            rel_path = os.path.join('recipes', package)
            resource_raw = resource_bytes_from_package(rel_path, folder_path)
            resource = Recipe.parse_raw(resource_raw)
            resource_version = RecipeVersion.from_resource(resource, rel_path)
            index.index_recipe_version(resource_version)

        return index

    @classmethod
    def index_resource(
        cls,
        index_folder: str,
        resource: Union[Operator, Recipe],
        path_to_readme: str = None,
        overwrite: bool = False,
    ):
        """Package an Operator or Workflow and add it to an existing index.yaml file

        Arguments:
            index_folder {str} -- The folder where the repository index is located
            resource {Union[Operator, Recipe]} -- The Operator or Recipe to package

        Keyword Arguments:
            overwrite {bool} -- Indicate whether overwriting an existing package or index entry is allowed (default: {False})

        Raises:
            ValueError: Error raised if the package already exists in the index file or directory
        """
        index_folder = os.path.abspath(index_folder)

        index_path = os.path.join(index_folder, 'index.yaml')

        index = cls.from_file(os.path.join(index_folder, 'index.yaml'))

        if isinstance(resource, Operator):
            type_path = 'operators'
            resource_version_class = OperatorVersion
        elif isinstance(resource, Recipe):
            type_path = 'recipes'
            resource_version_class = RecipeVersion
        else:
            raise ValueError(f"Resource should be an Operator or a Recipe")
        

        package_abs_path = package_resource(
            resource=resource,
            folder_path=os.path.join(index_folder, type_path),
            path_to_readme=path_to_readme,
            overwrite=overwrite
        )

        package_path = os.path.relpath(
            path=package_abs_path,
            start=os.path.commonprefix([index_folder, package_abs_path])    
        )

        resource_version = resource_version_class.from_resource(
            resource=resource,
            package_path=package_path
        )

        try:        
            if isinstance(resource, Operator):
                index.index_operator_version(resource_version, overwrite)
            elif isinstance(resource, Recipe):
                index.index_recipe_version(resource_version, overwrite)
        except ValueError as error:
            os.remove(package_abs_path)
            raise error

        index.to_yaml(index_path)


    @staticmethod
    def _index_resource_version(
        resource_dict: Dict[str, List[Union[RecipeVersion, OperatorVersion]]],
        resource_version: Union[RecipeVersion, OperatorVersion],
        overwrite: bool = False,
    ):
        resource_list = resource_dict.get(resource_version.name, [])

        if not overwrite:
            match = filter(lambda x: x.version == resource_version.version, resource_list)

            if next(match, None) is not None:
                raise ValueError(f'Resource {resource_version.name} already has a version {resource_version.index} in the index')

        resource_list.append(resource_version)
        resource_dict[resource_version.name] = resource_list

        return resource_dict

    def index_recipe_version(self, recipe_version: RecipeVersion, overwrite: bool = False):
        self.recipe = self._index_resource_version(self.recipe, recipe_version, overwrite)
        self.generated = datetime.utcnow()

    def index_operator_version(self, operator_version: OperatorVersion, overwrite: bool = False):
        self.operator = self._index_resource_version(self.operator, operator_version, overwrite)
        self.generated = datetime.utcnow()


    def package_by_version(
        self,
        package_type: str,
        package_name: str,
        package_version: str
    ) -> Union[OperatorVersion, RecipeVersion]:
        package_dict = getattr(self, package_type)

        package_list = package_dict.get(package_name)

        if package_list is None:
            raise ValueError(f'No {package_type} package with name {package_name} exists in this index')

        res = next(filter(lambda x: x.version == package_version, package_list), None)

        if res is None:
            raise ValueError(f'No {package_type} package with name {package_name} and version {package_version} exists in this index')

        return res

    def package_by_digest(
        self,
        package_type: str,
        package_name: str,
        package_digest: str
    ) -> Union[OperatorVersion, RecipeVersion]:
        package_dict = getattr(self, package_type)

        package_list = package_dict.get(package_name)

        if package_list is None:
            raise ValueError(f'No {package_type} package with name {package_name} exists in this index')

        res = next(filter(lambda x: x.digest == package_digest, package_list), None)

        if res is None:
            raise ValueError(f'No {package_type} package with name {package_name} and digest {package_digest} exists in this index')

        return res
