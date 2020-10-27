"""A collection of methods to handle queenbee referenced variables."""
from typing import Union
from .parser import parse_double_quotes_vars


def get_ref_variable(value: Union[bytes, str]) -> list:
    """Get referenced variable if any

    Arguments:
        value {Union[bytes, str]} -- input to parse double quoted variables
            ("{{some.double.quoted.var}}") from.

    Returns:
        list -- A list of matched substrings (empty list if None)
    """
    return parse_double_quotes_vars(value)


def validate_inputs_outputs_var_format(value: str) -> str:
    """Validate inputs/outputs variables

    Arguments:
        value {str} -- A '.' seperated string to be checked for inputs/outputs variable
            formatting

    Returns:
        str -- A string with validation error messages
    """
    add_info = ''
    parts = value.split('.')
    if len(parts) > 0 and parts[0] != 'inputs':
        add_info = f'Inputs and outputs variables can only refer to an input value' \
                   f' not: {parts[0]}'
    elif len(parts) != 2:
        add_info = 'Inputs and outputs variables must have 2 segments.'
    return add_info
