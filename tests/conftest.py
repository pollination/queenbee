import pytest
import os
import shutil
from urllib import request, parse


@pytest.fixture(autouse=True)
def temp_folder():
    os.mkdir('tests/assets/temp/')
    yield
    shutil.rmtree('tests/assets/temp')


@pytest.fixture(autouse=True)
def mock_repository_url(monkeypatch):

    repo_base_bath = 'tests/assets/repository'

    def urlopen_mock(req: request.Request):
        url = req.get_full_url()
        parsed = parse.urlparse(url)
        file_path = f'{repo_base_bath}{parsed.path}'
        return open(file_path, 'rb')

    monkeypatch.setattr(request, 'urlopen', urlopen_mock)
