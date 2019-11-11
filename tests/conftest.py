import pytest
import os
import shutil


@pytest.fixture(autouse=True)
def temp_folder():
    os.mkdir('tests/assets/temp/')
    yield
    shutil.rmtree('tests/assets/temp')
