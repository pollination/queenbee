"""Queenbee Task Operator class.

A task operator includes the information for executing tasks locally or in a container.
"""
from queenbee.schema.qutil import BaseModel
from pydantic import Field, validator
from typing import List, Any, Set
from enum import Enum


class Language(BaseModel):
    """Required programming language."""
    name: str = Field(
        'python',
        description='Language name'
    )
    
    version: str = Field(
        None,
        description='Language version requirements. For instance ==3.7 or >=3.6'
    )
    
    _valid_languages: Set[str] = set(['python', 'nodejs', 'bash'])

    # NOTE: yaml conversion doesn't play well with Enum. Use validators like this
    # instead.
    @validator('name')
    def check_language(cls, v):
        assert v.lower() in cls._valid_languages, \
            '{} is not a valid language. Try one of these languages:\n - {}'.format(
                v, '\n - '.join(cls._valid_languages)
            )
        return v.lower()


# TODO: This will most likely change. Too much to take on!
class App(BaseModel):
    """Local application."""
    name: str = Field(..., description='App name')

    version: str = Field(
        None,
        description='App version requirements. For instance >=5.2'
    )

    command: str = Field(
        ...,
        description='A command to check if application is installed'
    )

    pattern: str = Field(
        None,
        description='An optional regex pattern to apply to command output.'
    )


class Package(BaseModel):
    """A distribution package."""
    name: str = Field(..., description='Package name')

    version: str = Field(
        None,
        description='Package version requirements. For instance ==3.7 or >=3.6'
    )


class LocalRequirements(BaseModel):
    """Operator requirements for local runs."""
    type: Enum('Operator', {'type': 'Operator'}) = 'Operator'

    _valid_platforms: Set[str] = set(['linux', 'windows', 'mac'])

    platform: List[str] = Field(
        ['linux', 'windows', 'mac'],
        description='List of valid platforms that operator can execute the commands.'
        )

    language: List[Language] = Field(
        'bash',
        description='List of required programming languages to execute the commands'
            ' with an operator.'
        )

    # TODO: expand this to accept command to get the version and also add regex to parse
    # version from stdout
    app: List[App] = Field(
        None,
        description='List of applications that are required for operator to '
            'execute the commands locally. You must follow pip requirement specifiers: '
            'https://pip.pypa.io/en/stable/reference/pip_install/#requirement-specifiers'
            ' For instance use rtrace>=5.2 for radiance 5.2 or newer. Command will run '
            ' rtrace --version and tries to parse version from command.'
        )

    pip: List[Package] = Field(
        None,
        description='List of Python packages that are required for operator to '
            'execute the commands locally. You must follow pip requirement specifiers: '
            'https://pip.pypa.io/en/stable/reference/pip_install/#requirement-specifiers'
        )

    npm: List[Package] = Field(
        None,
        description='List of npm packages that are required for operator to '
            'execute the commands locally. You must follow npm install requirements: '
            'https://docs.npmjs.com/cli/install#synopsis'
        )

    # NOTE: yaml conversion doesn't play well with Enum hence using a validator.
    @validator('platform')
    def check_platform(cls, v):
        v = [x.lower() for x in v]

        for plat in v:
            assert plat in cls._valid_platforms, \
                '{} is not a valid platform. Try one of these platforms:\n - {}'.format(
                    plat, '\n - '.join(pl.title() for pl in cls._valid_platforms)
                )
        return v


class Operator(BaseModel):
    """Task operator.

    A task operator includes the information for executing tasks from command line
    or in a container.
    """
    type: Enum('Operator', {'type': 'Operator'}) = 'Operator'

    name: str = Field(
        ...,
        description='Operator name. This name should be unique among all the operators'
            ' in your workflow.'
        )

    version: str = Field(
        None,
        description='Optional version input for operator.'
    )

    image: str = Field(
        ...,
        description='Docker image name.'
    )

    local: LocalRequirements = Field(
        None,
        description='An optional requirement object to specify requirements for local'
            ' execution of the commands.'
        )
