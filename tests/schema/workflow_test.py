from queenbee.schema.workflow import Workflow


def test_load_workflow():
    # this import tests all the parts of workflow schema
    # not necessarily the best practice but it is fine since this
    # is the test for the schema and every other part has been already tested.
    fp = './tests/assets/workflow_example/daylightfactor.yaml'
    Workflow.from_file(fp)
