"""A collection of methods to handle queenbee referenced variables.

See README.md for a human readable version of valid variables.
"""
from .parser import parse_double_quotes_vars
from typing import List, Union


def get_ref_variable(value: Union[bytes, str]) -> List:
    """Get referenced variable if any."""
    return parse_double_quotes_vars(value)

def _validate_workflow_var_format(value: str):
    """Validate workflow vars."""
    add_info = ''
    parts = value.split('.')
    if len(parts) == 2:
        # workflow.id, workflow.name, item.field_name
        typ, attr = parts
        if attr not in ('name', 'id'):
            add_info = 'The only valid workflow variables with two segments' \
                ' are workflow.name and workflow.id.'
    elif len(parts) == 4:
        # workflow.inputs.parameters.<NAME>
        # workflow.inputs.artifacts.<NAME>
        # workflow.operators.<OPERATORNAME>.image
        typ, attr, prop, _ = parts
        if attr in ('inputs', 'outputs'):
            if prop not in ('parameters', 'artifacts'):
                add_info = 'Workflow inputs and outputs variables must be ' \
                    '"parameters" or "artifacts".'
        elif typ == 'operators':
            if typ[-1] != 'image':
                add_info = 'Workflow operator variable can only access ' \
                    'the image name.'
        else:
            add_info = 'Workflow variables must reference to "inputs", "outputs" ' \
                'or "operators".'
    else:
        add_info = 'Workflow variables are either 2 or 4 segments.'

    return add_info


def _validate_tasks_var_format(value: str):
    add_info = ''
    parts = value.split('.')
    if len(parts) != 5:
        add_info = 'Valid tasks variables are ' \
            '"tasks.<TASKNAME>.outputs.parameters.<NAME>" and ' \
            '"tasks.<TASKNAME>.outputs.artifacts.<NAME>".'
    # check for other parts
    _, _, attr, prop, _ = parts
    if attr != 'outputs':
        add_info = 'Tasks variable can only access previous tasks "outputs".'
    elif prop not in ('parameters', 'artifacts'):
        add_info = 'Task outputs variables must be "parameters" or "artifacts".'

    return add_info


def _validate_inputs_outputs_var_format(value: str):
    add_info = ''
    parts = value.split('.')
    if len(parts) != 3:
        add_info = 'Inputs and outputs variables must have 3 segments.'
    else:
        prop = parts[1]
        if prop not in ('parameters', 'artifacts'):
            add_info = 'Inputs and outputs variables must be "parameters" or' \
                ' "artifacts".'
    return add_info


def validate_ref_variable_format(value: str):
    """Ensure referenced values are formatted correctly."""
    add_info = ''
    if value.startswith('workflow.'):
        add_info = _validate_workflow_var_format(value)
    elif value.startswith('tasks.'):
        add_info = _validate_tasks_var_format(value)
    elif value.startswith('inputs.') or value.startswith('outputs.'):
        add_info = _validate_inputs_outputs_var_format(value)
    elif value.startswith('item'):
        pass
    else:
        add_info = 'Queenbee variable must start with workflow, tasks or items.'

    if add_info != '':
        msg = f'Invalid Queenbee variable: {value}.\n{add_info} ' \
            'See https://github.com/ladybug-tools/queenbee#variables' \
            ' for more information.'
        raise ValueError(msg)
    return True
