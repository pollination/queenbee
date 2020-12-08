"""Input objects for Queenbee jobs."""
from typing import Dict, List, Union

from pydantic import Field, constr

from ..artifact_source import HTTP, S3, ProjectFolder
from ...base.basemodel import BaseModel
from ...base.parser import parse_file


class JobArgument(BaseModel):
    """Job argument is an argument input for arguments which are not files or folders."""

    type: constr(regex='^JobArgument$') = 'JobArgument'

    name: str = Field(
        ...,
        description='Argument name. The name must match one of the input names from '
        'Job\'s DAG template.'
    )

    value: str = Field(
        ...,
        description='The value of the job argument.'
    )

    @property
    def is_artifact(self):
        return False

    @property
    def is_parameter(self):
        return not self.is_artifact


class JobPathArgument(BaseModel):
    type: constr(regex='^JobPathArgument$') = 'JobPathArgument'

    name: str = Field(
        ...,
        description='Argument name. The name must match one of the input names from '
        'Job\'s template which can be a function or DAG.'
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


JobArguments = Union[JobArgument, JobPathArgument]


def load_job_arguments(fp: str) -> List[JobArguments]:
    """Load Job arguments from a JSON or YAML file.

    Args:
        fp: File path to a JSON or YAML file with a list of JobArguments.

    Returns:
        List - A list of of JobArgument and JobPathArgument objects.
    """
    data = parse_file(fp)
    return load_job_arguments_from_dict(data)


def load_job_arguments_from_dict(data: List[Dict]) -> List[JobArguments]:
    """Load Job arguments from a list of dictionaries.

    Args:
        data: A list of job arguments as dictionaries.

    Returns:
        List - A list of of JobArgument and JobPathArgument objects.
    """
    args = []
    for d in data:
        try:
            arg_type = d['type']
        except KeyError:
            raise ValueError(
                'Input argument with missing "type" key. Valid types are: '
                f'JobArgument and JobPathArgument:\n{d}'
            )
        if arg_type == 'JobArgument':
            arg = JobArgument.parse_obj(d)
        elif arg_type == 'JobPathArgument':
            arg = JobPathArgument.parse_obj(d)
        else:
            raise ValueError(
                f'Invalid type for Job argument: {arg_type}.'
                'Valid types are: JobArgument and JobPathArgument.'
            )
        args.append(arg)

    return args
