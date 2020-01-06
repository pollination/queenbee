import pytest
from queenbee.schema.workflow import Workflow


def test_load_workflow():
    # this import tests all the parts of workflow schema
    # not necessarily the best practice but it is fine since this
    # is the test for the schema and every other part has been already tested.
    fp = './tests/assets/workflow_example/daylightfactor.yaml'
    wf = Workflow.from_file(fp)
    wf.validate_all()


def test_workflow_fetch_dict():
    fp = './tests/assets/workflow_example/daylightfactor.yaml'
    wf = Workflow.from_file(fp)

    output = wf.fetch_workflow_values('{{workflow.inputs.parameters.worker}}')

    assert output == {
        'workflow.inputs.parameters.worker': {
            'name': 'worker', 'path': None,
            'description': 'Maximum number of workers for executing this workflow.',
            'value': 1}
    }


def test_workflow_fetch_value():
    fp = './tests/assets/workflow_example/daylightfactor.yaml'
    wf = Workflow.from_file(fp)

    output = wf.fetch_workflow_values(
        '{{workflow.inputs.parameters.worker.value}}')

    assert output == {'workflow.inputs.parameters.worker.value': 1}


def test_workflow_fetch_multi():
    fp = './tests/assets/workflow_example/daylightfactor.yaml'
    wf = Workflow.from_file(fp)

    output = wf.fetch_workflow_values(
        '{{workflow.inputs.parameters.worker.value}}-something-{{workflow.operators.honeybee-radiance.image}}')

    assert output == {
        'workflow.inputs.parameters.worker.value': 1,
        'workflow.operators.honeybee-radiance.image': 'ladybugtools/honeybee-radiance'
    }


def test_hydrate_templates():
    fp = './tests/assets/workflow_example/daylightfactor.yaml'
    wf = Workflow.from_file(fp)

    wf.id = 'some-test-id'
    wf.inputs.parameters[1].value = 50
    wf.inputs.parameters[2].value = 'path/to/scene/files'

    wf_dict = wf.hydrate_workflow_templates()

    new_wf = Workflow.parse_obj(wf_dict)

    # Test string allocation
    assert new_wf.flow.tasks[2].arguments.parameters[0].value == 'path/to/scene/files'
    # Test number allocation
    assert new_wf.flow.tasks[1].arguments.parameters[0].value == 50
    # Test string concatenation
    assert new_wf.artifact_locations[0].root == "/path/to/test/some-test-id"


def test_hydrate__missing_value_error():
    fp = './tests/assets/workflow_example/daylightfactor.yaml'
    wf = Workflow.from_file(fp)

    with pytest.raises(AssertionError) as e:
        new_wf = wf.hydrate_workflow_templates()

    assert '{{workflow.inputs.parameters.sensor-count.value}} cannot reference an empty or null value.' in str(
        e)

def test_workflow_single_run_folder():
    """A workflow artifact locations should only contain one run folder"""
    fp = './tests/assets/workflow_example/double_run_folder.yaml'

    with pytest.raises(AssertionError) as e:
            wf = Workflow.from_file(fp)

    assert "Workflow can only have 1 run-folder artifact location" in str(e)
