"""Queenbee Function class."""
from typing import List
from pydantic import Field, validator

from ..io.common import IOBase
from ..io.function import FunctionInputs, FunctionOutputs
from ..base.variable import _validate_inputs_outputs_var_format, get_ref_variable


class Function(IOBase):
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

    inputs: List[FunctionInputs] = Field(
        None,
        description=u'Input arguments for this function.'
    )

    command: str = Field(
        ...,
        description=u'Full shell command for this function. Each function accepts only '
        'one command. The command will be executed as a shell command in operator. '
        'For running several commands after each other use && between the commands '
        'or pipe data from one to another using |'
    )

    outputs: List[FunctionOutputs] = Field(
        None,
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

    # @validator('inputs')
    # def validate_input_refs(cls, v):
    #     """Validate referenced variables in inputs"""
    #     if v is None:
    #         return []

    #     input_names = [param.name for param in v.parameters]

    #     variables = v.artifacts + v.parameters

    #     referenced_values = []

    #     for var in variables:
    #         ref_values = var.referenced_values
    #         for _, refs in ref_values.items():
    #             referenced_values.extend(refs)

    #     cls.validate_referenced_values(
    #         input_names=input_names,
    #         variables=referenced_values
    #     )

    #     return v

    # @validator('command')
    # def validate_command_refs(cls, v, values):
    #     """Validate referenced variables in the command"""

    #     ref_var = get_ref_variable(v)

    #     # If inputs is not in values it has failed validation
    #     # and we cannot check/validate output refs
    #     if 'inputs' not in values:
    #         return v

    #     inputs = values.get('inputs')

    #     input_names = [param.name for param in inputs.parameters]

    #     cls.validate_referenced_values(
    #         input_names=input_names,
    #         variables=ref_var
    #     )

    #     return v

    # @validator('outputs')
    # def validate_output_refs(cls, v, values):
    #     """Validate referenced variables in outputs"""
    #     if v is None:
    #         return []

    #     # If inputs is not in values it has failed validation
    #     # and we cannot check/validate output refs
    #     if 'inputs' not in values:
    #         return v

    #     inputs = values.get('inputs')

    #     input_names = [param.name for param in inputs.parameters]

    #     variables = v.artifacts + v.parameters

    #     referenced_values = []

    #     for var in variables:
    #         ref_values = var.referenced_values
    #         for _, refs in ref_values.items():
    #             referenced_values.extend(refs)

    #     cls.validate_referenced_values(
    #         input_names=input_names,
    #         variables=referenced_values
    #     )

    #     return v

    # @property
    # def artifacts(self) -> List[FunctionArtifact]:
    #     """List of workflow artifacts

    #     Returns:
    #         List[FunctionArtifact] -- A list of Input and Output artifacts from a
    #             function
    #     """
    #     artifacts = []

    #     if self.inputs and self.inputs.artifacts:
    #         artifacts.extend(self.inputs.artifacts)

    #     if self.outputs and self.outputs.artifacts:
    #         artifacts.extend(self.outputs.artifacts)

    #     return list(artifacts)
