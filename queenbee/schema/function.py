"""Queenbee Function class."""
from queenbee.schema.qutil import BaseModel
from queenbee.schema.parser import parse_double_quotes_vars as var_parser
from queenbee.schema.variable import validate_function_ref_variables
from pydantic import Field, validator, constr, root_validator
from typing import List, Dict
from enum import Enum
from queenbee.schema.arguments import Arguments
import warnings
import re


class Function(BaseModel):
    """A function with a single command."""
    type: constr(regex='^function$')

    name: str = Field(
        ...,
        description='Function name. Must be unique within a workflow.'
    )

    description: str = Field(
        None,
        description='Function description. A short human readable description for this function.'
    )

    inputs: Arguments = Field(
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

    operator: str = Field(
        ...,
        description='Function operator name.'
    )

    env: Dict[str, str] = Field(
        None,
        description='A dictionary of key:values for environmental variables.'
    )

    outputs: Arguments = Field(
        None,
        description='List of output arguments.'
    )

    @root_validator
    def validate_referenced_values(cls, values):
        """Validate referenced values in function.

        The validation checks are:
            * Reference to workflow values is not allowed in a function.
            * Referenced values are allowed in command and outputs. These values must
              reference to function inputs.
        """
        input_names = {'parameters': [], 'artifacts': []}
        inputs = values.get('inputs')
        if inputs:
            irf = inputs.ref_vars
            for key, value in irf.items():
                if len(value) == 0:
                    continue
                raise ValueError(
                    f'There is at least one referenced variable in inputs:\n'
                    f'{key}: {value}.\n'
                    f'Referenced values are not allowed in function inputs.'
                )

            if inputs.parameters:
                input_names['parameters'] = [p.name for p in inputs.parameters]
            if inputs.artifacts:
                input_names['artifacts'] = [p.name for p in inputs.artifacts]
        outputs = values.get('outputs')

        if outputs:
            # check output referenced values
            orf = outputs.ref_vars
            for rfv in orf.values():
                if len(rfv) != 0:
                    for vv in rfv:
                        for ovs in vv.values():
                            for ov_refs in ovs.values():
                                for ov in ov_refs:
                                    try:
                                        names = input_names[ov.split('.')[1]]
                                    except KeyError:
                                        names = []
                                    except:
                                        raise ValueError(
                                            f'Invalid referenced value: {ov}'
                                        )
                                validate_function_ref_variables(ov, names)
        # check command
        command = ' '.join(values.get('command').split())
        ref_vars = var_parser(command)
        for ref_var in ref_vars:
            try:
                names = input_names[ref_var.split('.')[1]]
            except KeyError:
                names = []  # invalid input. validate function will throw the error
            validate_function_ref_variables(ref_var, names)
        return values

    @property
    def artifacts(self):
        """List of workflow artifacts."""
        artifacts = []

        if self.inputs and self.inputs.artifacts:
            artifacts.extend(self.inputs.artifacts)

        if self.outputs and self.outputs.artifacts:
            artifacts.extend(self.outputs.artifacts)

        return list(artifacts)
