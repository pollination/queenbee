import os
from typing import List, Union, Dict
from datetime import datetime
from pydantic import Field, root_validator, validator, constr

from ..base.basemodel import BaseModel

from ..plugin import Plugin
from ..recipe import Recipe

from .package import PackageVersion


class RepositoryMetadata(BaseModel):

    type: constr(regex='^RepositoryMetadata$') = 'RepositoryMetadata'

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

    plugin_count: int = Field(
        0,
        description='The number of plugins hosted by the repository'
    )

    recipe_count: int = Field(
        0,
        description='The number of recipes hosted by the repository'
    )


class RepositoryIndex(BaseModel):
    """A searchable index for a Queenbee Plugin and Recipe repository"""
    api_version: constr(regex='^v1beta1$') = Field('v1beta1', readOnly=True)

    type: constr(regex='^RepositoryIndex$') = 'RepositoryIndex'

    generated: datetime = Field(
        None,
        description='The timestamp at which the index was generated'
    )

    metadata: RepositoryMetadata = Field(
        RepositoryMetadata(),
        description='Extra information about the repository'
    )

    plugin: Dict[str, List[PackageVersion]] = Field(
        {},
        description='A dict of plugins accessible by name. Each name key points to'
        ' a list of plugin versions'
    )

    recipe: Dict[str, List[PackageVersion]] = Field(
        {},
        description='A dict of recipes accessible by name. Each name key points to a'
        ' list of recipesversions'
    )

    @validator('plugin')
    def set_plugin_type(cls, v):
        for _, package in v.items():
            for pv in package:
                pv.kind = 'plugin'

        return v

    @validator('recipe')
    def set_recipe_type(cls, v):
        for _, package in v.items():
            for pv in package:
                pv.kind = 'recipe'

        return v

    @root_validator
    def metadata_counts(cls, values):
        values['metadata'].plugin_count = len(values.get('plugin'))
        values['metadata'].recipe_count = len(values.get('recipe'))

        return values

    @root_validator
    def check_slugs(cls, values):
        name = values.get('metadata').name

        if name is None:
            return values

        cls.add_slugs(
            root=name,
            packages=values.get('plugin')
        )

        cls.add_slugs(
            root=name,
            packages=values.get('recipe')
        )

        return values

    @classmethod
    def from_folder(cls, folder_path):
        """Generate a Repository Index from a folder

        This will scrape the folder for plugin and recipe packages and
        add their version information to the index.

        Arguments:
            folder_path {str} -- Path to a repository folder

        Returns:
            RepositoryIndex -- An index generated from packages in the folder
        """
        index = cls.parse_obj({})

        head, tail = os.path.split(folder_path)

        index.metadata.name = tail

        plugins_folder = os.path.join(folder_path, 'plugins')
        recipes_folder = os.path.join(folder_path, 'recipes')

        if os.path.exists(plugins_folder):
            for package in os.listdir(plugins_folder):
                package_path = os.path.join(folder_path, 'plugins', package)
                resource_version = PackageVersion.from_package(package_path)
                resource_version.url = \
                    os.path.join('plugins', package).replace('\\', '/')
                index.index_plugin_version(resource_version)

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
            packages=index.plugin,
        )

        cls.add_slugs(
            root=tail,
            packages=index.recipe,
        )

        index.metadata.plugin_count = len(index.plugin)
        index.metadata.recipe_count = len(index.recipe)

        return index

    @classmethod
    def index_resource(
        cls,
        index_folder: str,
        resource: Union[Plugin, Recipe],
        readme: str = None,
        license: str = None,
        overwrite: bool = False,
    ):
        """Package a plugin or Workflow and add it to an existing index.json file

        Arguments:
            index_folder {str} -- The folder where the repository index is located
            resource {Union[Plugin, Recipe]} -- The Plugin or Recipe to package

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

        if isinstance(resource, Plugin):
            type_path = 'plugins'
        elif isinstance(resource, Recipe):
            type_path = 'recipes'
        else:
            raise ValueError(f"Resource should be a plugin or a Recipe")

        resource_version, file_object = PackageVersion.package_resource(
            resource=resource,
            readme=readme,
            license=license,
        )

        tar_path = os.path.join(index_folder, type_path, resource_version.url)

        if isinstance(resource, Plugin):
            index.index_plugin_version(resource_version, overwrite)
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

    def index_plugin_version(self, plugin_version: PackageVersion,
                               overwrite: bool = False):
        """Add a Plugin Version to an Index of Plugins

        Arguments:
            plugin_version {PackageVersion} -- A plugin version object

        Keyword Arguments:
            overwrite {bool} -- Overwrite the Plugin Version if it already exists in
                the index (default: {False})
        """
        self.plugin = self._index_resource_version(
            self.plugin, plugin_version, overwrite=overwrite
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
        for package in os.listdir(os.path.join(folder_path, 'plugins')):
            package_path = os.path.join(folder_path, 'plugins', package)
            resource_version = PackageVersion.from_package(package_path)
            resource_version.url = \
                    os.path.join('plugins', package).replace('\\', '/')
            try:
                self.index_plugin_version(resource_version, overwrite)
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
        kind: str,
        package_name: str,
        package_tag: str
    ) -> PackageVersion:
        """Retrieve a Resource Version by its tag

        If the tag is set to "latest" then the most recent 
        version of the package will be retrieved.

        Arguments:
            kind {str} -- The type of package (plugin or recipe)
            package_name {str} -- The name of the package
            package_tag {str} -- The package tag

        Raises:
            ValueError: The package was not found

        Returns:
            PackageVersion -- A resource version object
        """
        package_dict = getattr(self, kind)

        package_list = package_dict.get(package_name)

        if package_list is None:
            raise ValueError(
                f'No {kind} package with name {package_name} exists'
                f' in this index'
            )

        if package_tag == 'latest':
            return self.get_latest(package_versions=package_list)

        res = next(filter(lambda x: x.tag == package_tag, package_list), None)

        if res is None:
            raise ValueError(
                f'No {kind} package with name {package_name} and version '
                f'{package_tag} exists in this index'
            )

        return res

    def package_by_digest(
        self,
        kind: str,
        package_name: str,
        package_digest: str
    ) -> PackageVersion:
        """Retrieve a Resource Version by its hash digest

        Arguments:
            kind {str} -- The type of package (plugin or recipe)
            package_name {str} -- The name of the package
            package_digest {str} -- The package digest

        Raises:
            ValueError: The package was not found

        Returns:
            PackageVersion -- A resource version object
        """
        package_dict = getattr(self, kind)

        package_list = package_dict.get(package_name)

        if package_list is None:
            raise ValueError(
                f'No {kind} package with name {package_name} exists'
                f' in this index'
            )

        res = next(filter(lambda x: x.digest ==
                          package_digest, package_list), None)

        if res is None:
            raise ValueError(
                f'No {kind} package with name {package_name} and digest '
                f'{package_digest} exists in this index'
            )

        return res

    def search(
        self,
        kind: str = None,
        search_string: str = None,
    ) -> List[PackageVersion]:
        """Search for a package inside of a repository using a search string

        Args:
            kind (str, optional): The type of package to search for
                (ie: plugin or recipe). Defaults to None.
            search_string (str, optional): The search string to use. Defaults to None.

        Returns:
            List[PackageVersion]: A list of packages (the latest from each list)
        """

        packages = []

        if kind is None or kind == 'recipe':
            for name, package_versions in self.recipe.items():
                package = self.get_latest(package_versions=package_versions)

                if package.search_match(search_string=search_string):
                    packages.append(package)

        if kind is None or kind == 'plugin':
            for name, package_versions in self.plugin.items():
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
            'plugin': {},
            'recipe': {},
        }

        for key in self.plugin:
            exclude_keys['plugin'][key] = {
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
