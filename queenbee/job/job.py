from datetime import datetime
from enum import Enum
from typing import Dict, Generator, List, Tuple, Union

from pydantic import Field, constr, validator
from pydantic.error_wrappers import ErrorWrapper, ValidationError

from ..base.basemodel import BaseModel
from ..io.inputs.dag import DAGInputs
from ..io.inputs.job import JobArgument, JobArguments, JobPathArgument
from ..recipe import Recipe


class Job(BaseModel):
    """Queenbee Job.

    A Job is an object to submit a list of arguments to execute a Queenbee recipe.
    """
    api_version: constr(regex='^v1beta1$') = Field('v1beta1', readOnly=True)

    type: constr(regex='^Job$') = 'Job'

    source: str = Field(
        ...,
        description='The source url for downloading the recipe.'
    )

    arguments: List[List[JobArguments]] = Field(
        None,
        description='Input arguments for this job.'
    )

    name: str = Field(
        None,
        description='An optional name for this job. This name will be used a the '
        'display name for the run.'
    )

    description: str = Field(
        None,
        description='Run description.'
    )

    labels: Dict[str, str] = Field(
        None,
        description='Optional user data as a dictionary. User data is for user reference'
        ' only and will not be used in the execution of the job.'
    )

    @validator('arguments', each_item=True)
    def check_duplicate_names(cls, v):
        argument_names = []
        for arg in v:
            if arg.name in argument_names:
                raise ValueError(f'duplicate argument name {arg.name}')
            argument_names.append(arg.name)

        return v

    def populate_default_arguments(self, inputs: List[DAGInputs]):
        for recipe_input in inputs:
            for combination in self.arguments:
                found_argument = False
                for argument in combination:
                    if argument.name == recipe_input.name:
                        found_argument = True

                if not found_argument and not recipe_input.required:
                    argument = None
                    if recipe_input.is_artifact and \
                            recipe_input.default is not None:
                        argument = JobPathArgument(
                            name=recipe_input.name,
                            source=recipe_input.default,
                        )
                    elif recipe_input.is_parameter:
                        argument = JobArgument(
                            name=recipe_input.name,
                            value=recipe_input.default,
                        )
                    if argument is not None:
                        combination.append(argument)

    def validate_arguments(self, inputs: List[DAGInputs]):
        errors = []
        for i, arg in enumerate(self.arguments):
            error_list = self._validate_argument_combination(arg, inputs)
            errors.extend([
                ErrorWrapper(error, ('arguments', i)) for error in error_list
            ])
        if len(errors) != 0:
            raise ValidationError(errors, self.__class__)

    def _validate_argument_combination(
            self,
            arguments: List[JobArguments],
            inputs: List[DAGInputs],
    ) -> List[ErrorWrapper]:
        errors = []

        for recipe_input in inputs:
            found_argument = False
            for argument in arguments:
                if argument.name == recipe_input.name:
                    found_argument = True
                    try:
                        self._check_argument_type(argument, recipe_input)
                    except Exception as err:
                        errors.append(err)

            if recipe_input.required and not found_argument:
                errors.append(ValueError(
                    f'missing required argument {recipe_input.name}'))

        return errors

    @staticmethod
    def _check_argument_type(argument: JobArguments, input: DAGInputs):
        if input.is_artifact and not isinstance(argument, JobPathArgument):
            raise ValueError(
                f'invalid argument type for {input.name}, '
                'should be "JobPathArgument"'
            )
        elif input.is_parameter and not isinstance(argument, JobArgument):
            raise ValueError(
                f'invalid argument type for {input.name}, '
                'should be "JobArgument"'
            )


class JobStatusEnum(str, Enum):
    """Enumaration of allowable status strings"""

    # The job has been created
    created = 'Created'
    # The job folder is being prepared for execution and runs are being scheduled
    pre_processing = 'Pre-Processing'
    # Runs have been scheduled
    running = 'Running'
    # The job has failed to schedule runs
    failed = 'Failed'
    # The job has been cancelled by a user
    cancelled = 'Cancelled'
    # All runs have either succeeded or failed
    completed = 'Completed'
    # Could not determine the status of the job
    unknown = 'Unknown'


class JobStatus(BaseModel):
    """Parametric Job Status."""

    api_version: constr(regex='^v1beta1$') = Field('v1beta1', readOnly=True)

    type: constr(regex='^JobStatus$') = 'JobStatus'

    id: str = Field(
        ...,
        description='The ID of the individual job.'
    )

    status: JobStatusEnum = Field(
        JobStatusEnum.unknown,
        description='The status of this job.'
    )

    message: str = Field(
        None,
        description='Any message produced by the job. Usually error/debugging hints.'
    )

    started_at: datetime = Field(
        ...,
        description='The time at which the job was started'
    )

    finished_at: datetime = Field(
        None,
        description='The time at which the task was completed'
    )

    source: str = Field(
        None,
        description='Source url for the status object. It can be a recipe or a function.'
    )

    runs_pending: int = Field(
        0,
        description='The count of runs that are pending'
    )

    runs_running: int = Field(
        0,
        description='The count of runs that are running'
    )

    runs_completed: int = Field(
        0,
        description='The count of runs that have completed'
    )

    runs_failed: int = Field(
        0,
        description='The count of runs that have failed'
    )

    runs_cancelled: int = Field(
        0,
        description='The count of runs that have been cancelled'
    )
