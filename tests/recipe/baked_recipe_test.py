import os
import pytest
from tests.base._base import BaseTestClass

from queenbee.recipe import BakedRecipe, Recipe

ASSET_FOLDER = 'tests/assets/recipes'


class TestFolder(BaseTestClass):
    asset_folder = ASSET_FOLDER

    def pytest_generate_tests(self, metafunc):

        folders = self.class_folders()

        recipes = self.fixture_instances('valid', Recipe)

        invalid_recipe_paths = self.fixture_files('baked-invalid')
        invalid_recipe_paths = [
            recipe_path for recipe_path in invalid_recipe_paths if recipe_path.endswith('yaml')]

        parametrized = []

        for f in invalid_recipe_paths:
            parametrized.append((f, f))

        if "folder" in metafunc.fixturenames:
            metafunc.parametrize('folder', folders, ids=[
                                 os.path.basename(folder) for folder in folders])
            # metafunc.parametrize("folder,instance", inputs, ids=[os.path.basename(input_tuple[0]) for input_tuple in inputs])

        if 'recipe' in metafunc.fixturenames:
            metafunc.parametrize('recipe', recipes, ids=[
                                 recipe.metadata.name for recipe in recipes])

        if 'invalid_recipe' in metafunc.fixturenames and 'error_message' not in metafunc.fixturenames:

            metafunc.parametrize('invalid_recipe', invalid_recipe_paths, ids=[
                                 os.path.basename(rec_path) for rec_path in invalid_recipe_paths])

        if 'invalid_recipe' in metafunc.fixturenames and 'error_message' in metafunc.fixturenames:

            metafunc.parametrize(
                'invalid_recipe, error_message',
                parametrized,
                indirect=['error_message'],
                ids=[os.path.basename(rec_path)
                     for rec_path in invalid_recipe_paths],
            )

    def class_folders(self):
        return self.fixture_folders('folders')

    def recipe_instances(self):
        return self.fixture_instances('valid', Recipe)

    def test_from_folder(self, folder):
        parsed_instance = BakedRecipe.from_folder(folder)

        parsed_test_path = os.path.join(
            ASSET_FOLDER, 'baked', f'{parsed_instance.metadata.name}.yaml')
        if os.path.exists(parsed_test_path):
            compare_instance = BakedRecipe.from_file(parsed_test_path)

            assert compare_instance == parsed_instance

    def test_from_recipe_instance(self, recipe):
        parsed_instance = BakedRecipe.from_recipe(recipe)

    @pytest.fixture(scope='function')
    def error_message(self, request):
        file_path, _ = os.path.splitext(request.param)
        error_message_path = '.'.join([file_path, 'error'])
        try:
            with open(error_message_path, 'r') as f:
                return f.read()
        except:
            pytest.skip(
                f'Cannot read value error message at path: {error_message_path}')

    def test_raise_value_error(self, invalid_recipe):
        invalid_recipe = Recipe.from_file(invalid_recipe)
        with pytest.raises(ValueError):
            BakedRecipe.from_recipe(invalid_recipe)

    def test_value_error_message(self, invalid_recipe, error_message):
        invalid_recipe = Recipe.from_file(invalid_recipe)
        with pytest.raises(ValueError, match=error_message):
            BakedRecipe.from_recipe(invalid_recipe)
