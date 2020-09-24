"""Queenbee Function class."""
from typing import Dict, List
from pydantic import Field, validator

from ..base.basemodel import BaseModel
from ..base.io import IOBase
from ..base.variable import _validate_inputs_outputs_var_format, get_ref_variable


class FunctionArtifact(BaseModel):
    """A Function Artifact object

    This indicates the path within the function context at which a certain file or folder
    (ie: artifact) can be found.
    """

    name: str = Field(
        ...,
        description='Name of the artifact. Must be unique within a task\'s '
        'inputs / outputs.'
    )

    description: str = Field(
        None,
        description='Optional description for input parameter.'
    )

    path: str = Field(
        ...,
        description='Path to the artifact relative to the working directory where the'
        ' command is executed.'
    )

    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        """Get referenced variables if any

        Returns:
            Dict[str, List[str]] -- A dictionary where keys are attributes and lists '
                'contain referenced value string
        """
        return self._referenced_values(['path'])


class FunctionParameterIn(BaseModel):
    """A Function Parameter

    Parameter indicate a passed string parameter to a service template with an optional
    default value.
    """

    name: str = Field(
        ...,
        description='Name is the parameter name. must be unique within a task\'s '
        'inputs.'
    )

    default: str = Field(
        None,
        description='Default value to use for an input parameter if a value was not'
        ' supplied.'
    )

    description: str = Field(
        None,
        description='Optional description for input parameter.'
    )

    required: bool = Field(
        None,
        description='Whether this value must be specified in a task argument.'
    )

    @validator('required', always=True)
    def validate_required(cls, v, values):
        """Ensure parameter with no default value is marked as required"""
        function_name = values.get('name')
        default = values.get('default')

        # No default value provided and required not specified
        # Set required to True
        if default is None and v is None:
            return True

        # Default value provided and required not specified
        # Set required to False
        if default is not None and v is None:
            return False

        # No default value but explicitely set to not required
        if default is None and v is False:
            raise ValueError(
                f'{function_name}: required should be true if no default is provided'
            )

        return v

    @property
    def referenced_values(self) -> Dict[str, List[str]]:
        """Get referenced variables if any"""
        return self._referenced_values(['default'])


class FunctionParameterOut(FunctionArtifact):

    pass


class FunctionInputs(IOBase):
    """The Inputs of a Function"""

    parameters: List[FunctionParameterIn] = Field(
        [],
        description=''
    )

    artifacts: List[FunctionArtifact] = Field(
        [],
        description=''
    )


class FunctionOutputs(IOBase):
    """The Outputs of a Function"""

    parameters: List[FunctionParameterOut] = Field(
        [],
        description=''
    )

    artifacts: List[FunctionArtifact] = Field(
        [],
        description=''
    )


class Function(BaseModel):
    """A Function with a single command"""

    name: str = Field(
        ...,
        description='Function name. Must be unique within an operator.'
    )

    description: str = Field(
        None,
        description='Function description. A short human readable description for'
        ' this function.'
    )

    inputs: FunctionInputs = Field(
        FunctionInputs(),
        description=u'Input arguments for this function.'
    )

    command: str = Field(
        ...,
        description=u'Full shell command for this function. Each function accepts only '
        'one command. The command will be executed as a shell command in operator. '
        'For running several commands after each other use && between the commands '
        'or pipe data from one to another using |'
    )

    outputs: FunctionOutputs = Field(
        FunctionOutputs(),
        description='List of output arguments.'
    )

    @staticmethod
    def validate_referenced_values(input_names: List[str], variables: List):
        """Validate referenced values

        Arguments:
            input_names {List[str]} -- A list of acceptable names to reference
            variables {List} -- A list of referenced value strings ("x.y.z")

        Raises:
            ValueError: One of the reference variables is invalid
        """
        if not variables:
            return

        warns = []
        for ref in variables:
            ref = ref.replace('{{', '').replace('}}', '').strip()
            add_info = _validate_inputs_outputs_var_format(ref)

            if not add_info:
                # check the value exist in inputs
                name = ref.split('.')[-1]
                if name not in input_names:
                    warns.append(
                        f'\t- {{{{{ref}}}}}: Cannot find "{name}" in inputs.')
            else:
                warns.append(add_info)

        if warns != []:
            info = '\n'.join(warns)
            msg = f'Invalid referenced value(s) in function:\n{info}'
            raise ValueError(msg)

    @validator('inputs')
    def validate_input_refs(cls, v):
        """Validate referenced variables in inputs"""

        input_names = [param.name for param in v.parameters]

        variables = v.artifacts + v.parameters

        referenced_values = []

        for var in variables:
            ref_values = var.referenced_values
            for _, refs in ref_values.items():
                referenced_values.extend(refs)

        cls.validate_referenced_values(
            input_names=input_names,
            variables=referenced_values
        )

        return v

    @validator('command')
    def validate_command_refs(cls, v, values):
        """Validate referenced variables in the command"""

        ref_var = get_ref_variable(v)

        # If inputs is not in values it has failed validation
        # and we cannot check/validate output refs
        if 'inputs' not in values:
            return v

        inputs = values.get('inputs')

        input_names = [param.name for param in inputs.parameters]

        cls.validate_referenced_values(
            input_names=input_names,
            variables=ref_var
        )

        return v

    @validator('outputs')
    def validate_output_refs(cls, v, values):
        """Validate referenced variables in outputs"""

        # If inputs is not in values it has failed validation
        # and we cannot check/validate output refs
        if 'inputs' not in values:
            return v

        inputs = values.get('inputs')

        input_names = [param.name for param in inputs.parameters]

        variables = v.artifacts + v.parameters

        referenced_values = []

        for var in variables:
            ref_values = var.referenced_values
            for _, refs in ref_values.items():
                referenced_values.extend(refs)

        cls.validate_referenced_values(
            input_names=input_names,
            variables=referenced_values
        )

        return v

    @property
    def artifacts(self) -> List[FunctionArtifact]:
        """List of workflow artifacts

        Returns:
            List[FunctionArtifact] -- A list of Input and Output artifacts from a
                function
        """
        artifacts = []

        if self.inputs and self.inputs.artifacts:
            artifacts.extend(self.inputs.artifacts)

        if self.outputs and self.outputs.artifacts:
            artifacts.extend(self.outputs.artifacts)

        return list(artifacts)
