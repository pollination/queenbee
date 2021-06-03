from typing import List

import pytest
from pydantic.main import ValidationError
from queenbee.io.artifact_source import HTTP
from queenbee.io.inputs.dag import DAGInputs, DAGPathInput, DAGStringInput
from queenbee.job import Job


@pytest.fixture
def optional_parameter_input():
    return DAGStringInput(
        name='optional-parameter-input',
        required=False,
        default='some-default-value'
    )


@pytest.fixture
def required_parameter_input():
    return DAGStringInput(
        name='required-parameter-input',
        required=True,
    )


@pytest.fixture
def optional_artifact_input():
    return DAGPathInput(
        name='optional-artifact-input',
        required=False,
        default=HTTP(url='https://some.url.com/path/to/artifact')
    )


@pytest.fixture
def optional_artifact_input_with_no_default():
    return DAGPathInput(
        name='optional-artifact-input-no-default',
        required=False,
    )


@pytest.fixture
def required_artifact_input():
    return DAGPathInput(
        name='required-artifact-input',
        required=True,
    )


@pytest.fixture
def required_inputs(required_parameter_input, required_artifact_input):
    return [required_parameter_input, required_artifact_input]


@pytest.fixture
def optional_inputs(optional_parameter_input, optional_artifact_input,
                    optional_artifact_input_with_no_default):
    return [
        optional_parameter_input,
        optional_artifact_input,
        optional_artifact_input_with_no_default
    ]


@pytest.fixture
def all_inputs(required_inputs, optional_inputs):
    return required_inputs + optional_inputs


def test_duplicated_job_arguments():
    with pytest.raises(ValidationError) as validation_err:
        Job.parse_obj({
            'source': 'https://example.com/registries/recipe/daylight-factor/latest',
            'arguments': [[
                {
                    'type': 'JobArgument',
                    'name': 'sensor-grid-count',
                    'value': 200
                },
                {
                    'type': 'JobPathArgument',
                    'name': 'sensor-grid-count',
                    'source': {
                        'type': 'ProjectFolder',
                        'path': 'some/path'
                    }
                },
                {
                    'type': 'JobPathArgument',
                    'name': 'model_hbjson',
                    'source': {
                        'type': 'ProjectFolder',
                        'path': 'some/path'
                    }
                }
            ]]
        })

    assert validation_err.value.errors() == [{
        'loc': ('arguments', 0),
        'msg': 'duplicate argument name sensor-grid-count',
        'type': 'value_error'
    }]


def test_valid_job_arguments(all_inputs: List[DAGInputs]):
    job: Job = Job.parse_obj({
        'source': 'https://example.com/registries/recipe/daylight-factor/latest',
        'arguments': [[
            {
                'type': 'JobArgument',
                'name': 'required-parameter-input',
                'value': 'some-string'
            },
            {
                'type': 'JobArgument',
                'name': 'optional-parameter-input',
                'value': 'some-string'
            },
            {
                'type': 'JobPathArgument',
                'name': 'required-artifact-input',
                'source': {
                    'type': 'ProjectFolder',
                    'path': 'some/path'
                }
            },
            {
                'type': 'JobPathArgument',
                'name': 'optional-artifact-input',
                'source': {
                    'type': 'ProjectFolder',
                    'path': 'some/path'
                }
            },
        ]]
    })

    job.validate_arguments(all_inputs)


def test_required_job_arguments_missing(all_inputs: List[DAGInputs]):
    job: Job = Job.parse_obj({
        'source': 'https://example.com/registries/recipe/daylight-factor/latest',
        'arguments': [[
            {
                'type': 'JobPathArgument',
                'name': 'input-grid',
                'source': {
                    'type': 'ProjectFolder',
                    'path': 'some/path'
                }
            },
            {
                'type': 'JobPathArgument',
                'name': 'model_hbjson',
                'source': {
                    'type': 'ProjectFolder',
                    'path': 'some/path'
                }
            }
        ], [
            {
                'type': 'JobPathArgument',
                'name': 'required-artifact-input',
                'source': {
                    'type': 'ProjectFolder',
                    'path': 'some/path'
                }
            },
        ]]
    })

    with pytest.raises(ValidationError) as validation_err:
        job.validate_arguments(all_inputs)

    assert validation_err.value.errors() == [
        {
            'loc': ('arguments', 0),
            'msg': 'missing required argument required-parameter-input',
            'type': 'value_error'
        }, {
            'loc': ('arguments', 0),
            'msg': 'missing required argument required-artifact-input',
            'type': 'value_error'
        }, {
            'loc': ('arguments', 1),
            'msg': 'missing required argument required-parameter-input',
            'type': 'value_error'
        }
    ]


def test_invalid_job_arguments_type(all_inputs: List[DAGInputs]):
    job: Job = Job.parse_obj({
        'source': 'https://example.com/registries/recipe/daylight-factor/latest',
        'arguments': [[
            {
                'type': 'JobArgument',
                'name': 'required-parameter-input',
                'value': 'some-string'
            },
            {
                'type': 'JobPathArgument',
                'name': 'optional-parameter-input',
                'source': {
                    'type': 'ProjectFolder',
                    'path': 'some/path'
                }
            },
            {
                'type': 'JobPathArgument',
                'name': 'required-artifact-input',
                'source': {
                    'type': 'ProjectFolder',
                    'path': 'some/path'
                }
            },
        ], [
            {
                'type': 'JobArgument',
                'name': 'required-parameter-input',
                'value': 'some-string'
            },
            {
                'type': 'JobArgument',
                'name': 'required-artifact-input',
                'value': 'some-string'
            },
        ]]
    })

    with pytest.raises(ValidationError) as validation_err:
        job.validate_arguments(all_inputs)

    assert validation_err.value.errors() == [
        {
            'loc': ('arguments', 0),
            'msg': 'invalid argument type for optional-parameter-input, should be "JobArgument"',
            'type': 'value_error'
        },
        {
            'loc': ('arguments', 1),
            'msg': 'invalid argument type for required-artifact-input, should be "JobPathArgument"',
            'type': 'value_error'
        },
    ]


def test_populate_optional_arguments(optional_inputs: List[DAGInputs]):
    job: Job = Job.parse_obj({
        'source': 'https://example.com/registries/recipe/daylight-factor/latest',
        'arguments': [[
            {
                'type': 'JobArgument',
                'name': 'optional-parameter-input',
                'value': 'some-string'
            }
        ], [
            {
                'type': 'JobPathArgument',
                'name': 'optional-artifact-input',
                'source': {
                    'type': 'ProjectFolder',
                    'path': 'some/path'
                }
            }
        ]]
    })

    job.populate_default_arguments(optional_inputs)

    expected_job = Job.parse_obj({
        'source': 'https://example.com/registries/recipe/daylight-factor/latest',
        'arguments': [[
            {
                'type': 'JobArgument',
                'name': 'optional-parameter-input',
                'value': 'some-string'
            },
            {
                'type': 'JobPathArgument',
                'name': 'optional-artifact-input',
                'source': {
                    'type': 'HTTP',
                    'url': 'https://some.url.com/path/to/artifact'
                }
            }
        ], [
            {
                'type': 'JobPathArgument',
                'name': 'optional-artifact-input',
                'source': {
                    'type': 'ProjectFolder',
                    'path': 'some/path'
                }
            },
            {
                'type': 'JobArgument',
                'name': 'optional-parameter-input',
                'value': 'some-default-value'
            },
        ]]
    })

    assert job == expected_job
