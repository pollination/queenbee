"""Parse workflow files from JSON / YAML files with support for import_from key."""
import json
import yaml
import os
import re


def _check_list(lst, folder):
    for item in lst:
        if isinstance(item, list):
            _check_list(item, folder)
        elif isinstance(item, dict):
            _import_dict_data(item, folder)


def _import_dict_data(dictionary, folder):
    """find import_from keys if any.

    Args:
        dictionary: Input dictionary to be parsed.
        folder: Starting folder for relative paths in dictionary.
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


def parse_file(input_file):
    """Parse queenbee objects from an input JSON or YAML file.

    This method will replace 'import_from' keys with the content from files recursively. 

    Args:
        input_file: A YAML or JSON input file.

    Returns:
        The content of the input file as a dictionary.
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


def parse_double_quotes_vars(input):
    """Parse values between {{ }}."""
    pattern = r"{{\s*([_a-zA-Z0-9.\-\$#\?]*)\s*}}"
    match = re.findall(pattern, input, flags=re.MULTILINE)
    return match


def parse_double_quote_workflow_vars(input):
    """Parse values between {{ workflow. }}."""
    pattern = r"{{\s*(workflow\.[_a-zA-Z0-9.\-\$#\?]*)\s*}}"
    match = re.findall(pattern, input, flags=re.MULTILINE)
    return match


def replace_double_quote_vars(text, key, replace):
    """Take an input string with template keys and replace them"""
    pattern = r"{{\s*" + key + r"\s*}}"
    return re.sub(pattern, replace, text)
