import pytest
from tests.base.io_test import BaseIOTest
from tests.base.value_error import BaseValueErrorTest

from pydantic.error_wrappers import ValidationError

from queenbee.schema.workflow import Workflow


class TestIO(BaseIOTest):

    klass = Workflow

class TestValueError(BaseValueErrorTest):

    klass = Workflow

def test_get_parameter():
    fp = './tests/assets/Workflow/valid/daylightfactor.yaml'
    wf = Workflow.from_file(fp)
    par = wf.get_inputs_parameter('sensor-grid-name')
    assert par.value == 'room'
    par = wf.get_inputs_parameter('worker')
    assert par.value == 1


def test_get_artifact():
    fp = './tests/assets/Workflow/valid/daylightfactor.yaml'
    wf = Workflow.from_file(fp)
    with pytest.raises(ValueError, match='Arguments has no artifacts'):
        wf.get_inputs_artifact('sensor-grid-name')


def test_get_operator():
    fp = './tests/assets/Workflow/valid/daylightfactor.yaml'
    wf = Workflow.from_file(fp)
    opt = wf.get_operator('honeybee-radiance')
    assert opt.image == 'ladybugtools/honeybee-radiance'
    with pytest.raises(ValueError, match='Invalid operator name: honeybee'):
        wf.get_operator('honeybee')


def test_get_template():
    fp = './tests/assets/Workflow/valid/daylightfactor.yaml'
    wf = Workflow.from_file(fp)
    template = wf.get_template('generate-sky')
    assert template.type == 'function'
    assert template.operator == 'honeybee-radiance'


def test_get_task():
    fp = './tests/assets/Workflow/valid/daylightfactor.yaml'
    wf = Workflow.from_file(fp)
    t = wf.get_task('daylight-factor-simulation')
    assert t.template == 'ray-tracing'
    assert len(t.dependencies) == 2


def test_workflow_fetch_value():
    fp = './tests/assets/Workflow/valid/daylightfactor.yaml'
    wf = Workflow.from_file(fp)

    output = wf.fetch_workflow_values('{{workflow.inputs.parameters.worker}}')

    assert output == {'workflow.inputs.parameters.worker': 1}


def test_workflow_fetch_multi():
    fp = './tests/assets/Workflow/valid/daylightfactor.yaml'
    wf = Workflow.from_file(fp)

    output = wf.fetch_workflow_values(
        '{{workflow.inputs.parameters.worker}}-something'
        '-{{workflow.operators.honeybee-radiance.image}}')

    assert output == {
        'workflow.inputs.parameters.worker': 1,
        'workflow.operators.honeybee-radiance.image': 'ladybugtools/honeybee-radiance'
    }


def test_update_input_parameters_values():
    fp = './tests/assets/Workflow/valid/daylightfactor.yaml'
    wf = Workflow.from_file(fp)
    values = {
        'parameters': {
            'worker': {'value': 6},
            'sensor-grid-name': {'value': 'classroom'}
        }
    }
    wf.update_inputs_values(values)
    assert wf.inputs.get_parameter_value('worker') == 6
    assert wf.inputs.get_parameter_value('sensor-grid-name') == 'classroom'


def test_hydrate_templates():
    fp = './tests/assets/Workflow/valid/daylightfactor.yaml'
    wf = Workflow.from_file(fp)

    wf.id = 'some-test-id'
    wf.inputs.parameters[1].value = 50
    wf.inputs.parameters[2].value = 'path/to/scene/files'

    # wf_dict = wf.hydrate_workflow_templates()

    # _ = Workflow.parse_obj(wf_dict)

    # TODO: Put the tests back after rewriting hydrate workflow
    # Test string allocation
    # assert new_wf.flow.tasks[2].arguments.parameters[0].value == 'path/to/scene/files'
    # Test number allocation
    # assert new_wf.flow.tasks[1].arguments.parameters[0].value == 50
    # Test string concatenation
    # assert new_wf.artifact_locations[0].root == "/path/to/test/some-test-id"


def test_hydrate_missing_value_error():
    fp = './tests/assets/Workflow/valid/daylightfactor.yaml'
    wf = Workflow.from_file(fp)

    err_msg = '{{workflow.inputs.parameters.sensor-grid-count}} cannot reference an' \
        ' empty or null value'
    with pytest.raises(AssertionError, match=err_msg):
        wf.hydrate_workflow_templates()

