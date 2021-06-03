import pytest
from pydantic.main import ValidationError
from queenbee.job import Job

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
