from datetime import datetime
from enum import Enum
from typing import Dict, List, Union
from typing import Literal

from pydantic import Field, field_validator
from pydantic import ValidationError
from pydantic_core import InitErrorDetails
from ..base.basemodel import BaseModel
from ..io.inputs.dag import DAGInputs
from ..io.inputs.job import JobArgument, JobArguments, JobPathArgument


class Job(BaseModel):
    """Queenbee Job.

    A Job is an object to submit a list of arguments to execute a Queenbee recipe.
    """
    api_version: Literal['v1beta1'] = Field('v1beta1', json_schema_extra={'readOnly': True})

    type: Literal['Job'] = 'Job'

    source: str = Field(
        ...,
        description='The source url for downloading the recipe.'
    )

    arguments: Union[List[List[JobArguments]], None] = Field(
        None,
        description='Input arguments for this job.'
    )

    name: Union[str, None] = Field(
        None,
        description='An optional name for this job. This name will be used a the '
        'display name for the run.'
    )

    description: Union[str, None] = Field(
        None,
        description='Run description.'
    )

    labels: Union[Dict[str, str], None] = Field(
        None,
        description='Optional user data as a dictionary. User data is for user reference'
        ' only and will not be used in the execution of the job.'
    )

    @field_validator('arguments')
    @classmethod
    def check_duplicate_names(cls, v: List[List[JobArguments]]):
        if v is None:
            return v
        for arg_list in v:
            argument_names = []
            for arg in arg_list:
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
        errors: List[InitErrorDetails] = []
        
        for i, arg in enumerate(self.arguments):
            # Assuming this returns a list of Exceptions or error strings
            error_list = self._validate_argument_combination(arg, inputs)
            
            for error in error_list:
                # In V2, we define errors as dictionaries (InitErrorDetails)
                errors.append(
                    InitErrorDetails(
                        type='value_error',  # Standard error type
                        loc=('arguments', i),
                        msg=str(error),      # Convert the exception/error to a string message
                        input=arg,            # The value that caused the error
                        ctx={'error': error}
                    )
                )

        if errors:
            # V2 method to raise validation errors manually
            raise ValidationError.from_exception_data(self.__class__.__name__, errors)

    def _validate_argument_combination(
        self, arguments: List[JobArguments], inputs: List[DAGInputs]
    ) -> List[ValueError]:
        errors = []

        for recipe_input in inputs:
            found_argument = False
            for argument in arguments:
                if argument.name == recipe_input.name:
                    found_argument = True
                    try:
                        self._check_argument_type(argument, recipe_input)
                    except ValueError as err:
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

    api_version: Literal['v1beta1'] = Field('v1beta1', json_schema_extra={'readOnly': True})

    type: Literal['JobStatus'] = 'JobStatus'

    id: str = Field(
        ...,
        description='The ID of the individual job.'
    )

    status: JobStatusEnum = Field(
        JobStatusEnum.unknown,
        description='The status of this job.'
    )

    message: Union[str, None] = Field(
        None,
        description='Any message produced by the job. Usually error/debugging hints.'
    )

    started_at: datetime = Field(
        ...,
        description='The time at which the job was started'
    )

    finished_at: Union[datetime, None] = Field(
        None,
        description='The time at which the task was completed'
    )

    source: Union[str, None] = Field(
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
