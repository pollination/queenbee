from queenbee.schema.artifact_location import InputFolderLocation, RunFolderLocation, HTTPLocation, S3Location
from queenbee.schema.qutil import BaseModel
from typing import List, Union
import yaml


class ArtifactLocationReader(BaseModel):

    artifact_locations: List[Union[InputFolderLocation,
                                   RunFolderLocation, HTTPLocation, S3Location]]


def test_create_run_folder_location():
    loc_dict = {
        'name': 'local-test',
        'type': 'run-folder',
        'root': 'C:\\Users\\Test\\Projects\\Project 1'
    }

    loc = RunFolderLocation.parse_obj(loc_dict)

    loc_file = './tests/assets/temp/run_location.yaml'
    loc.to_yaml(loc_file)

    # parse the yaml file and compare the two
    with open(loc_file) as inf:
        obj = yaml.safe_load(inf.read())

    assert obj == loc.to_dict()


def test_create_input_folder_location():
    loc_dict = {
        'name': 'local-test',
        'type': 'input-folder',
        'root': 'C:\\Users\\Test\\Projects\\Project 1'
    }

    loc = InputFolderLocation.parse_obj(loc_dict)

    loc_file = './tests/assets/temp/input_location.yaml'
    loc.to_yaml(loc_file)

    # parse the yaml file and compare the two
    with open(loc_file) as inf:
        obj = yaml.safe_load(inf.read())

    assert obj == loc.to_dict()


def test_create_http_location():
    loc_dict = {
        'name': 'http-test',
        'type': 'http',
        'root': 'http://climate.onebuilding.org',
        'headers': {
            'Authorization': 'some-long-JWT-token'
        }
    }

    loc = HTTPLocation.parse_obj(loc_dict)

    loc_file = './tests/assets/temp/http_location.yaml'
    loc.to_yaml(loc_file)

    # parse the yaml file and compare the two
    with open(loc_file) as inf:
        obj = yaml.safe_load(inf.read())

    assert obj == loc.to_dict()


def test_create_s3_location():
    loc_dict = {
        'name': 's3-test',
        'type': 's3',
        'root': 'pollination',
        'endpoint': 's3.eu-west-1.amazonaws.com',
        'bucket': 'all-of-my-data',
        'credentials_path': 'C:\\Users\\Test\\.queenbee\\config.yaml'
    }

    loc = S3Location.parse_obj(loc_dict)

    loc_file = './tests/assets/temp/s3_location.yaml'
    loc.to_yaml(loc_file)

    # parse the yaml file and compare the two
    with open(loc_file) as inf:
        obj = yaml.safe_load(inf.read())

    assert obj == loc.to_dict()


def test_load_artifact_locations():
    locs = ArtifactLocationReader.from_file(
        './tests/assets/artifact_locations.yaml')

    local_dict = {
        'name': 'local-test',
        'type': 'run-folder',
        'root': 'C:\\Users\\Test\\Projects\\Project 1'
    }

    http_dict = {
        'name': 'http-test',
        'type': 'http',
        'root': 'http://climate.onebuilding.org',
        'headers': {
            'Authorization': 'some-long-JWT-token'
        }
    }
    s3_dict = {
        'name': 's3-test',
        'type': 's3',
        'root': 'pollination',
        'endpoint': 's3.eu-west-1.amazonaws.com',
        'bucket': 'all-of-my-data',
        'credentials_path': 'C:\\Users\\Test\\.queenbee\\config.yaml'
    }

    locs.artifact_locations[0].to_dict() == local_dict
    locs.artifact_locations[2].to_dict() == http_dict
    locs.artifact_locations[2].to_dict() == s3_dict
