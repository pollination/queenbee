"""Queenbee Arguments class.

Arguments includes the input arguments to a task or a workflow.

Queenbee accepts two types of arguments:

    1. Parameters: A ``parameter`` is a variable that can be passed to a task or a
        workflow.
    2. Artifact: An ``artifact`` is a file or folder that can be identified by a url or
        a path.
"""
from queenbee.schema.qutil import BaseModel, find_dup_items
from queenbee.schema.artifact_location import VerbEnum
import queenbee.schema.variable as qbvar
from pydantic import Field, root_validator
from typing import List, Any, Optional, Dict


class Parameter(BaseModel):
    """Parameter.

    Parameter indicate a passed string parameter to a service template with an optional
    default value.
    """
    name: str = Field(
        ...,
        description='Name is the parameter name. must be unique within a task\'s '
        'inputs / outputs.'
    )

    value: Any = Field(
        None,
        description='Default value to use for an input parameter if a value was not'
        ' supplied.'
    )

    description: str = Field(
        None,
        description='Optional description for input parameter.'
    )

    path: str = Field(
        None,
        description='Load parameters values from a JSON file.'
    )

    @root_validator
    def validate_vars(cls, values):
        """Validate input values."""
        name = values.get('name')
        value = values.get('value')
        path = values.get('path')
        if value and path:
            raise ValueError(
                f'You should either set value or path for parameter {name}.'
            )

        value = value if value is not None else path
        if not value or isinstance(value, (int, float)):
            return values
        # check if it is a referenced variable
        ref_var = qbvar.get_ref_variable(value)

        if ref_var:
            for rv in ref_var:
                qbvar.validate_ref_variable_format(rv)

        return values

    @property
    def current_value(self):
        """Try to get the current value.

        This method checks the ``value`` property first and if it is None it will return
        the value for ``path``.
        """
        return self.value if self.value is not None else self.path

    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        """Get referenced variables if any.

        """
        value = self.current_value
        if not value or isinstance(value, (int, float)):
            return {}

        ref_var = qbvar.get_ref_variable(value)
        if not ref_var:
            return {}

        return {'value': ref_var} if self.value is not None else {'path': ref_var}


class Artifact(BaseModel):
    """Artifact indicates an artifact to be placed at a specified path."""

    name: str = Field(
        ...,
        description='Name of the artifact. Must be unique within a task\'s '
        'inputs / outputs.'
    )

    location: str = Field(
        None,  # is it possible to create an artifact with no artifact location?
        description="Name of the artifact_location to source this artifact from."
    )

    source_path: str = Field(
        None,
        description='Path to the artifact in a url or S3 bucket.'
    )

    path: str = Field(
        None,
        description='Path to the artifact relative to the run-folder artifact location.'
    )

    description: str = Field(
        None,
        description='Optional description for input parameter.'
    )

    headers: Optional[Dict[str, str]] = Field(
        None,
        description='An object with Key Value pairs of HTTP headers. '
        'For artifacts from URL location only.'
    )

    verb: Optional[VerbEnum] = Field(
        None,
        description='The HTTP verb to use when making the request. '
        'For artifacts from URL location only.'
    )

    @root_validator
    def validate_vars(cls, values):
        """Validate input values."""
        input_values = [
            v for v in (
                values.get('location'), values.get('path'),
                values.get('source_path')
            ) if v is not None
        ]

        if not input_values:
            return values

        for value in values:
            # check if it is a referenced variable
            ref_var = qbvar.get_ref_variable(value)
            if not ref_var:
                continue
            for rv in ref_var:
                qbvar.validate_ref_variable_format(rv)

        return values

    @property
    def current_value(self):
        """Try to get the current value.

        This method checks the ``path`` property first and if it is None it will return
        the value for ``source_path``.
        """
        return self.path if self.path is not None else self.source_path

    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        """Get referenced variables if any."""
        ref_values = {}
        values = [
            v for v in (self.location, self.path, self.source_path)
            if v is not None
        ]

        if not values:
            return ref_values

        for value in values:
            ref_var = qbvar.get_ref_variable(value)
            if ref_var:
                ref_values[value] = ref_var

        return ref_values


class Arguments(BaseModel):
    """Arguments to a task or a workflow.

    Queenbee accepts two types of arguments: parameters and artifacts. A ``parameter``
    is a variable that can be passed to a task or a workflow. An ``artifact`` is a file
    or folder that can be identified by a url or a path.
    """

    parameters: List[Parameter] = Field(
        None,
        description='Parameters is the list of input parameters to pass to the task '
        'or workflow. A parameter can have a default value which will be overwritten if '
        'an input value is provided.'
    )

    artifacts: List[Artifact] = Field(
        None,
        description='Artifacts is the list of file and folder arguments to pass to the '
        'task or workflow.'
    )

    @root_validator
    def unique_names(cls, values):
        params = values.get('parameters')
        if params:
            param_names = [par.name for par in params]
            if len(param_names) != len(set(param_names)):
                dup = find_dup_items(param_names)
                raise ValueError(f'Duplicate parameter names: {dup}')
        artifacts = values.get('artifacts')
        if artifacts:
            artifact_names = [par.name for par in artifacts]
            if len(artifact_names) != len(set(artifact_names)):
                dup = find_dup_items(artifact_names)
                raise ValueError(f'Duplicate artifact names: {dup}')
        return values

    def get_parameter(self, name):
        """Get a parameter by name."""
        param = [par for par in self.parameters if par.name == name]
        if not param:
            raise ValueError(f'Invalid parameter name: {name}')
        return param[0]

    def get_artifact(self, name):
        """Get an artifact by name."""
        if not self.artifacts:
            raise ValueError('Arguments has no artifacts')
        param = [par for par in self.artifacts if par.name == name]
        if not param:
            raise ValueError(f'Invalid artifact name: {name}')
        return param[0]

    def get_parameter_value(self, name):
        """Get a parameter value by name."""
        return self.get_parameter(name).current_value

    def get_artifact_value(self, name):
        """Get an artifact value by name."""
        return self.get_artifact(name).current_value

    def set_parameter_value(self, name, value):
        """Set a parameter value.

        Args:
            name: Parameter name.
            value: A dictionary ``{name_1: value_1, name_2: value_2}``.
        """
        parameter = self.get_parameter(name)
        for k, v in value.items():
            setattr(parameter, k, v)

    def set_artifact_value(self, name, value):
        """Set a artifact value.

        Args:
            name: Artifact name.
            value: A dictionary ``{name_1: value_1, name_2: value_2}``.
        """
        artifact = self.get_artifact(name)
        for k, v in value.items():
            setattr(artifact, k, v)

    @property
    def referenced_values(self):
        """Get list of referenced values in parameters and artifacts."""
        ref_values = {'artifacts': [], 'parameters': []}
        if self.artifacts:
            ref_values['artifacts'] = [
                {art.name: art.referenced_values} for art in self.artifacts
                if art.referenced_values
            ]
        if self.parameters:
            ref_values['parameters'] = [
                {par.name: par.referenced_values} for par in self.parameters
                if par.referenced_values
            ]

        return ref_values
