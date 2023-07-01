"""Queenbee Function class."""
from enum import Enum
from typing import List
from pydantic import Field, validator, constr, root_validator, NoneStr

from ..io.common import IOBase
from ..io.inputs.function import FunctionInputs
from ..io.outputs.function import FunctionOutputs
from ..base.variable import get_ref_variable, validate_inputs_outputs_var_format


class ScriptingLanguages(str, Enum):
    """Supported Scripting Languages"""
    Python = 'python'


class Function(IOBase):
    """A Function with a single or a script."""

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

    command: NoneStr = Field(
        None,
        description=u'Full shell command for this function. Each function accepts only '
        'one command. The command will be executed as a shell command in plugin. '
        'For running several commands after each other use && between the commands '
        'or pipe data from one to another using |'
    )

    language: ScriptingLanguages = Field(
        ScriptingLanguages.Python,
        description='Programming language of the script. Currently only Python is '
        'supported.'
    )

    source: NoneStr = Field(
        None,
        description='Source contains the source code of the script to execute.'
    )

    @property
    def is_script(self):
        """Returns True if this Function is a script function."""
        if self.source:
            return True
        return False

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

    @validator('command', 'source')
    def validate_command_refs(cls, v, values):
        """Validate referenced variables in the command"""
        if not v:
            return

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

    @root_validator(skip_on_failure=True)
    def check_either_source_or_command(cls, values):
        """Validate either source or command is provided"""
        command = values.get('command')
        source = values.get('source')
        if command or source:
            return values

        # validation failed
        name = values.get('name')
        raise ValueError(
            f'Invalid Function: {name}. Either command or source must be provided.'
        )
