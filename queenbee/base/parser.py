"""Parse workflow files from JSON / YAML files with support for ``import_from`` key."""
import json
import yaml
import os
import re


def _check_list(lst: list, folder: str):
    """Recursive function to handle import_from inside nested lists."""
    for item in lst:
        if isinstance(item, list):
            _check_list(item, folder)
        elif isinstance(item, dict):
            _import_dict_data(item, folder)


def _import_dict_data(dictionary: dict, folder: str) -> dict:
    """Find import_from keys if any.

    Arguments:
        dictionary {dict} -- Input dictionary to be parsed
        folder {str} -- Starting folder for relative paths in dictionary

    Returns:
        dict -- a dictionary with imported pointed data
    """

    for key, value in dictionary.items():
        if key == 'import_from':
            if not os.path.isabs(value):
                value = os.path.join(folder, value)
            # replace import_from with dictionary data from the input file
            dictionary[key] = parse_file(value)
        elif isinstance(value, dict):
            _import_dict_data(value, folder)
        elif isinstance(value, list):
            #  a list of items
            _check_list(value, folder)

    if 'import_from' in dictionary:
        # update values but not the ones that are already there
        for key, value in dictionary['import_from'].items():
            if key not in dictionary:
                dictionary[key] = value
        del(dictionary['import_from'])

    return dictionary


def parse_file(input_file: str) -> dict:
    """Parse queenbee objects from an input JSON or YAML file.

    This method will replace 'import_from' keys with the content from files recursively.

    Args:
        input_file {str} -- A YAML or JSON input file.

    Returns:
        dict -- The content of the input file as a dictionary.
    """
    input_file = os.path.abspath(input_file)

    assert os.path.isfile(input_file), 'Failed to find {}'.format(input_file)

    ext = input_file.split('.')[-1].lower()
    assert ext in ('json', 'yml', 'yaml'), \
        'Invalid input file type: [{}]. Only JSON and YAML files are valid.'.format(
            ext)

    if ext == 'json':
        with open(input_file) as inf:
            data = json.load(inf)
    else:
        with open(input_file) as inf:
            data = yaml.safe_load(inf.read())

    # populate full dictionary
    folder = os.path.dirname(input_file)
    return _import_dict_data(data, folder)


def parse_double_quotes_vars(input: str) -> list:
    """Parse values between {{ }}

    Arguments:
        input {str} -- A string to parse doubled quoted vars from

    Returns:
        list -- A list of matched substrings (empty list if None)
    """
    pattern = r"{{\s*([_a-zA-Z0-9.\-\$#\?]*)\s*}}"
    match = re.findall(pattern, input, flags=re.MULTILINE)
    return match


def parse_double_quote_workflow_vars(input: str) -> list:
    """Parse values between {{workflow.*}}

    Arguments:
        input {str} -- A string to parse doubled quoted vars from

    Returns:
        list -- A list of matched substrings (empty list if None)
    """
    pattern = r"{{\s*(workflow\.[_a-zA-Z0-9.\-\$#\?]*)\s*}}"
    match = re.findall(pattern, input, flags=re.MULTILINE)
    return match


def replace_double_quote_vars(text: str, key: str, replace: str) -> str:
    """Take an input string with template keys and replace them

    Arguments:
        text {str} -- The string to replace values from
        key {str} -- The key to match and replace
        replace {str} -- The value to replace the matched key with

    Returns:
        str -- A string with replaced substrings
    """
    pattern = r"{{\s*" + key + r"\s*}}"
    return re.sub(pattern, replace, text)
