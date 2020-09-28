import os
from typing import List, Union, Dict
from datetime import datetime
from pydantic import Field, root_validator, validator

from ..base.basemodel import BaseModel

from ..operator import Operator
from ..recipe import Recipe

from .package import PackageVersion


class RepositoryMetadata(BaseModel):

    name: str = Field(
        None,
        description='The name of the repository'
    )

    description: str = Field(
        'A Queenbee package repository',
        description='A short description of the repository'
    )

    source: str = Field(
        None,
        description='The source path (url or local) to the repository'
    )

    operator_count: int = Field(
        0,
        description='The number of operators hosted by the repository'
    )

    recipe_count: int = Field(
        0,
        description='The number of recipes hosted by the repository'
    )


class RepositoryIndex(BaseModel):
    """A searchable index for a Queenbee Operator and Recipe repository"""

    generated: datetime = Field(
        None,
        description='The timestamp at which the index was generated'
    )

    metadata: RepositoryMetadata = Field(
        RepositoryMetadata(),
        description='Extra information about the repository'
    )

    operator: Dict[str, List[PackageVersion]] = Field(
        {},
        description='A dict of operators accessible by name. Each name key points to'
        ' a list of operator versions'
    )

    recipe: Dict[str, List[PackageVersion]] = Field(
        {},
        description='A dict of recipes accessible by name. Each name key points to a'
        ' list of recipesversions'
    )

    @validator('operator')
    def set_operator_type(cls, v):
        for _, package in v.items():
            for pv in package:
                pv.type = 'operator'

        return v

    @validator('recipe')
    def set_recipe_type(cls, v):
        for _, package in v.items():
            for pv in package:
                pv.type = 'recipe'

        return v

    @root_validator
    def metadata_counts(cls, values):
        values['metadata'].operator_count = len(values.get('operator'))
        values['metadata'].recipe_count = len(values.get('recipe'))

        return values

    @root_validator
    def check_slugs(cls, values):
        name = values.get('metadata').name

        if name is None:
            return values

        cls.add_slugs(
            root=name,
            packages=values.get('operator')
        )

        cls.add_slugs(
            root=name,
            packages=values.get('recipe')
        )

        return values

    @classmethod
    def from_folder(cls, folder_path):
        """Generate a Repository Index from a folder

        This will scrape the folder for operator and recipe packages and
        add their version information to the index.

        Arguments:
            folder_path {str} -- Path to a repository folder

        Returns:
            RepositoryIndex -- An index generated from packages in the folder
        """
        index = cls.parse_obj({})

        head, tail = os.path.split(folder_path)

        index.metadata.name = tail

        operators_folder = os.path.join(folder_path, 'operators')
        recipes_folder = os.path.join(folder_path, 'recipes')

        if os.path.exists(operators_folder):
            for package in os.listdir(operators_folder):
                package_path = os.path.join(folder_path, 'operators', package)
                resource_version = PackageVersion.from_package(package_path)
                resource_version.url = \
                    os.path.join('operators', package).replace('\\', '/')
                index.index_operator_version(resource_version)

        if os.path.exists(recipes_folder):
            for package in os.listdir(recipes_folder):
                package_path = os.path.join(folder_path, 'recipes', package)
                resource_version = PackageVersion.from_package(package_path)
                resource_version.url = \
                    os.path.join('recipes', package).replace('\\', '/')
                index.index_recipe_version(resource_version)

        index.generated = datetime.utcnow()

        cls.add_slugs(
            root=tail,
            packages=index.operator,
        )

        cls.add_slugs(
            root=tail,
            packages=index.recipe,
        )

        index.metadata.operator_count = len(index.operator)
        index.metadata.recipe_count = len(index.recipe)

        return index

    @classmethod
    def index_resource(
        cls,
        index_folder: str,
        resource: Union[Operator, Recipe],
        readme: str = None,
        license: str = None,
        overwrite: bool = False,
    ):
        """Package an Operator or Workflow and add it to an existing index.json file

        Arguments:
            index_folder {str} -- The folder where the repository index is located
            resource {Union[Operator, Recipe]} -- The Operator or Recipe to package

        Keyword Arguments:
            readme {str} -- Text of the recipe README.md file if it exists
                (default: {None})
            license {str} -- Text of the resource LICENSE file if it exists
                (default: {None})
            overwrite {bool} -- Indicate whether overwriting an existing package or
                index entry is allowed (default: {False})

        Raises:
            ValueError: Error raised if the package already exists in the index file or
                directory
        """
        index_folder = os.path.abspath(index_folder)

        index_path = os.path.join(index_folder, 'index.json')

        index = cls.from_file(os.path.join(index_folder, 'index.json'))

        if isinstance(resource, Operator):
            type_path = 'operators'
        elif isinstance(resource, Recipe):
            type_path = 'recipes'
        else:
            raise ValueError(f"Resource should be an Operator or a Recipe")

        resource_version, file_object = PackageVersion.package_resource(
            resource=resource,
            readme=readme,
            license=license,
        )

        tar_path = os.path.join(index_folder, type_path, resource_version.url)

        if isinstance(resource, Operator):
            index.index_operator_version(resource_version, overwrite)
        elif isinstance(resource, Recipe):
            index.index_recipe_version(resource_version, overwrite)

        # Write packaged version to repo directory
        with open(tar_path, 'wb') as f:
            file_object.seek(0)
            f.write(file_object.read())

        index.to_json(index_path)

    @staticmethod
    def add_slugs(root: str, packages: Dict[str, List[PackageVersion]]):
        """Add slugs to the packages based on the provided root

        Args:
            root (str): a slug root string
            packages (Dict[str, List[PackageVersion]]): The list of packages to update with slugs
        """
        for _, package_list in packages.items():
            for p in package_list:
                p.slug = f'{root}/{p.name}'

    @staticmethod
    def get_latest(package_versions: List[PackageVersion]) -> PackageVersion:
        """Get the most recent package from the given list

        Args:
            package_versions (List[PackageVersion]): A list of Queenbee packages

        Returns:
            PackageVersion: The most recent Queenbee package in the list
        """
        if package_versions == []:
            return None

        package_versions.sort(key=lambda x: x.created)
        return package_versions[-1]

    @staticmethod
    def _index_resource_version(
        resource_dict: Dict[str, List[PackageVersion]],
        resource_version: PackageVersion,
        repository_name: str = None,
        overwrite: bool = False,
    ) -> Dict[str, List[PackageVersion]]:
        """Add a resource version to an index of resource versions

        Arguments:
            resource_dict {Dict[str, List[PackageVersion]]} -- An
                index of resource versions
            resource_version {PackageVersion} -- The resource
                version to add

        Keyword Arguments:
            repository_name {str} -- The name of the repository the package is being indexed to
                (default: {None})
            overwrite {bool} -- Overwrite a resource version if it already exists
                (default: {False})

        Raises:
            ValueError: Resource version already exists

        Returns:
            Dict[str, List[PackageVersion]] -- A resource version
                index
        """
        if repository_name:
            resource_version.slug = f'{repository_name.lower()}/{resource_version.name.lower()}'

        resource_list = resource_dict.get(resource_version.name, [])

        if not overwrite:
            match = next(
                filter(
                    lambda x: x.tag == resource_version.tag, resource_list
                ), None
            )
            if match is not None:
                if match.digest != resource_version.digest:
                    raise ValueError(
                        f'Resource {resource_version.name} already has a version'
                        f' {resource_version.tag} in the index'
                    )
                return resource_dict

        resource_list = list(
            filter(lambda x: x.tag != resource_version.tag, resource_list)
        )

        resource_list.append(resource_version)
        resource_dict[resource_version.name] = resource_list

        return resource_dict

    def index_recipe_version(self, recipe_version: PackageVersion,
                             overwrite: bool = False):
        """Add a Recipe Version to an Index of Recipes

        Arguments:
            recipe_version {PackageVersion} -- A recipe version object

        Keyword Arguments:
            overwrite {bool} -- Overwrite the Recipe Version if it already exists in the
                index (default: {False})
        """
        self.recipe = self._index_resource_version(
            self.recipe, recipe_version, overwrite=overwrite
        )
        self.generated = datetime.utcnow()

    def index_operator_version(self, operator_version: PackageVersion,
                               overwrite: bool = False):
        """Add a Operator Version to an Index of Operators

        Arguments:
            operator_version {PackageVersion} -- A operator version object

        Keyword Arguments:
            overwrite {bool} -- Overwrite the Operator Version if it already exists in
                the index (default: {False})
        """
        self.operator = self._index_resource_version(
            self.operator, operator_version, overwrite=overwrite
        )
        self.generated = datetime.utcnow()

    def merge_folder(self, folder_path, overwrite: bool = False, skip: bool = False):
        """Merge the contents of a repository folder with the index

        Arguments:
            folder_path {str} -- The path to the repository folder

        Keyword Arguments:
            overwrite {bool} -- Overwrite any Resource Version (default: {False})
            skip {bool} -- Skip any errors if version already exist (default: {False})

        Raises:
            ValueError: Resource version already exists or is invalid
        """
        for package in os.listdir(os.path.join(folder_path, 'operators')):
            package_path = os.path.join(folder_path, 'operators', package)
            resource_version = PackageVersion.from_package(package_path)
            resource_version.url = \
                    os.path.join('operators', package).replace('\\', '/')
            try:
                self.index_operator_version(resource_version, overwrite)
            except ValueError as error:
                if 'already has a version ' in str(error):
                    if skip:
                        continue
                raise error

        for package in os.listdir(os.path.join(folder_path, 'recipes')):
            package_path = os.path.join(folder_path, 'recipes', package)
            resource_version = PackageVersion.from_package(package_path)
            resource_version.url = \
                    os.path.join('recipes', package).replace('\\', '/')
            try:
                self.index_recipe_version(resource_version, overwrite)
            except ValueError as error:
                if 'already has a version ' in str(error):
                    if skip:
                        continue
                raise error

    def package_by_tag(
        self,
        package_type: str,
        package_name: str,
        package_tag: str
    ) -> PackageVersion:
        """Retrieve a Resource Version by its tag

        If the tag is set to "latest" then the most recent 
        version of the package will be retrieved.

        Arguments:
            package_type {str} -- The type of package (operator or recipe)
            package_name {str} -- The name of the package
            package_tag {str} -- The package tag

        Raises:
            ValueError: The package was not found

        Returns:
            PackageVersion -- A resource version object
        """
        package_dict = getattr(self, package_type)

        package_list = package_dict.get(package_name)

        if package_list is None:
            raise ValueError(
                f'No {package_type} package with name {package_name} exists'
                f' in this index'
            )

        if package_tag == 'latest':
            return self.get_latest(package_versions=package_list)

        res = next(filter(lambda x: x.tag == package_tag, package_list), None)

        if res is None:
            raise ValueError(
                f'No {package_type} package with name {package_name} and version '
                f'{package_tag} exists in this index'
            )

        return res

    def package_by_digest(
        self,
        package_type: str,
        package_name: str,
        package_digest: str
    ) -> PackageVersion:
        """Retrieve a Resource Version by its hash digest

        Arguments:
            package_type {str} -- The type of package (operator or recipe)
            package_name {str} -- The name of the package
            package_digest {str} -- The package digest

        Raises:
            ValueError: The package was not found

        Returns:
            PackageVersion -- A resource version object
        """
        package_dict = getattr(self, package_type)

        package_list = package_dict.get(package_name)

        if package_list is None:
            raise ValueError(
                f'No {package_type} package with name {package_name} exists'
                f' in this index'
            )

        res = next(filter(lambda x: x.digest ==
                          package_digest, package_list), None)

        if res is None:
            raise ValueError(
                f'No {package_type} package with name {package_name} and digest '
                f'{package_digest} exists in this index'
            )

        return res

    def search(
        self,
        package_type: str = None,
        search_string: str = None,
    ) -> List[PackageVersion]:
        """Search for a package inside of a repository using a search string

        Args:
            package_type (str, optional): The type of package to search for (ie: operator or recipe). Defaults to None.
            search_string (str, optional): The search string to use. Defaults to None.

        Returns:
            List[PackageVersion]: A list of packages (the latest from each list)
        """

        packages = []

        if package_type is None or package_type == 'recipe':
            for name, package_versions in self.recipe.items():
                package = self.get_latest(package_versions=package_versions)

                if package.search_match(search_string=search_string):
                    packages.append(package)

        if package_type is None or package_type == 'operator':
            for name, package_versions in self.operator.items():
                package = self.get_latest(package_versions=package_versions)

                if package.search_match(search_string=search_string):
                    packages.append(package)

        return packages

    def json(self, *args, **kwargs):
        """Overwrite the BaseModel json method to exclude certain keys

        The objective is to remove the readme, license and manifest keys which are not
        needed in a serialized index object.
        """
        exclude_keys = {
            'operator': {},
            'recipe': {},
        }

        for key in self.operator:
            exclude_keys['operator'][key] = {
                '__all__': {
                    'readme',
                    'license',
                    'manifest'
                }
            }

        for key in self.recipe:
            exclude_keys['recipe'][key] = {
                '__all__': {
                    'readme',
                    'license',
                    'manifest'
                }
            }

        return super(RepositoryIndex, self).json(exclude=exclude_keys, *args, **kwargs)
