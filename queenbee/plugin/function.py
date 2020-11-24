"""Queenbee Function class."""
from typing import List
from pydantic import Field, validator, constr

from ..io.common import IOBase
from ..io.inputs.function import FunctionInputs
from ..io.outputs.function import FunctionOutputs
from ..base.variable import validate_inputs_outputs_var_format, get_ref_variable


class Function(IOBase):
    """A Function with a single command"""

    type: constr(regex='^Function$') = 'Function'

    name: str = Field(
        ...,
        description='Function name. Must be unique within a plugin.'
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

    outputs: List[FunctionOutputs] = Field(
        None,
        description='List of output arguments.'
    )

    command: str = Field(
        ...,
        description=u'Full shell command for this function. Each function accepts only '
        'one command. The command will be executed as a shell command in plugin. '
        'For running several commands after each other use && between the commands '
        'or pipe data from one to another using |'
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
            add_info = validate_inputs_outputs_var_format(ref)

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

    @validator('command')
    def validate_command_refs(cls, v, values):
        """Validate referenced variables in the command"""

        ref_var = get_ref_variable(v)

        # If inputs is not in values it has failed validation
        # and we cannot check/validate output refs
        if 'inputs' not in values:
            return v

        inputs = values.get('inputs')

        input_names = [param.name for param in inputs]

        cls.validate_referenced_values(
            input_names=input_names,
            variables=ref_var
        )

        return v
