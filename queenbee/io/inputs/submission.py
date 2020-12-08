"""Input objects for SimulationSubmission."""
from typing import Dict, List, Union

from pydantic import Field, constr

from ..artifact_source import HTTP, S3, ProjectFolder
from ...base.basemodel import BaseModel
from ...base.parser import parse_file


class SubmissionArgument(BaseModel):
    """Submission argument for parameter inputs that are not files or folders."""

    type: constr(regex='^SubmissionArgument$') = 'SubmissionArgument'

    name: str = Field(
        ...,
        description='Argument name. The name must match one of the input names from '
        'Submission\'s DAG template.'
    )

    value: str = Field(
        ...,
        description='The value of the submission argument.'
    )

    @property
    def is_artifact(self):
        return False

    @property
    def is_parameter(self):
        return not self.is_artifact


class SubmissionPathArgument(BaseModel):
    type: constr(regex='^SubmissionPathArgument$') = 'SubmissionPathArgument'

    name: str = Field(
        ...,
        description='Argument name. The name must match one of the input names from '
        'Submission\'s template which can be a function or DAG.'
    )

    source: Union[HTTP, S3, ProjectFolder] = Field(
        ...,
        description='The path to source the file from.'
    )

    @property
    def is_artifact(self):
        return True

    @property
    def is_parameter(self):
        return not self.is_artifact


SubmissionArguments = Union[SubmissionArgument, SubmissionPathArgument]


def load_submission_arguments(fp: str) -> List[SubmissionArguments]:
    """Load Submission arguments from a JSON or YAML file.

    Args:
        fp: File path to a JSON or YAML file with a list of SubmissionArguments.

    Returns:
        List - A list of of SubmissionArgument and SubmissionPathArgument objects.
    """
    data = parse_file(fp)
    return load_submission_arguments_from_dict(data)


def load_submission_arguments_from_dict(data: List[Dict]) -> List[SubmissionArguments]:
    """Load Submission arguments from a list of dictionaries.

    Args:
        data: A list of submission arguments as dictionaries.

    Returns:
        List - A list of of SubmissionArgument and SubmissionPathArgument objects.
    """
    args = []
    for d in data:
        try:
            arg_type = d['type']
        except KeyError:
            raise ValueError(
                'Input argument with missing "type" key. Valid types are: '
                f'SubmissionArgument and SubmissionPathArgument:\n{d}'
            )
        if arg_type == 'SubmissionArgument':
            arg = SubmissionArgument.parse_obj(d)
        elif arg_type == 'SubmissionPathArgument':
            arg = SubmissionPathArgument.parse_obj(d)
        else:
            raise ValueError(
                f'Invalid type for Submission argument: {arg_type}.'
                'Valid types are: SubmissionArgument and SubmissionPathArgument.'
            )
        args.append(arg)

    return args
