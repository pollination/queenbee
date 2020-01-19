import pytest
from queenbee.schema.dag import DAG, DAGTask
from pydantic.error_wrappers import ValidationError


def test_load_from_file():
    fp = './tests/assets/flow.yaml'
    dag = DAG.from_file(fp)
    assert dag.name == 'arrival'
    assert len(dag.tasks) == 4


def test_load_wrong_target():
    fp = './tests/assets/flow_with_wrong_target.yaml'
    with pytest.raises(ValueError, match=r'Invalid target.*put-on-shoes'):
        DAG.from_file(fp)


def test_load_invalid_loop():
    fp = './tests/assets/flow_invalid_loop.yaml'
    with pytest.raises(ValueError, match=r'loop.*no argument'):
        DAG.from_file(fp)
