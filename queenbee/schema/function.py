"""Queenbee Function class."""
from queenbee.schema.qutil import BaseModel
from queenbee.schema.parser import parse_double_quotes_vars as var_parser
from pydantic import Schema, validator, constr
from typing import List, Dict
from enum import Enum
from queenbee.schema.arguments import Arguments
import warnings
import re


class Function(BaseModel):
    """A function with a single command."""
    type: constr(regex='^function$')

    name: str = Schema(
        ...,
        description='Function name. Must be unique within a workflow.'
    )

    description: str = Schema(
        None,
        description='Function description. A short human readable description for this function.'
    )

    inputs: Arguments = Schema(
        None,
        description=u'Input arguments for this function.'
    )

    # TODO: This will end up being an issue. command here is what args really are in
    # docker. Changing this to args will be confusing. Keep it as command will also be
    # confusing if one wants to match it with container
    command: str = Schema(
        ...,
        description=u'Full shell command for this function. Each function accepts only '
        'one command. The command will be executed as a shell command in operator. '
        'For running several commands after each other use && between the commands '
        'or pipe data from one to another using |'
    )

    operator: str = Schema(
        ...,
        description='Function operator name.'
    )

    env: Dict[str, str] = Schema(
        None,
        description='A dictionary of key:values for environmental variables.'
    )

    outputs: Arguments = Schema(
        None,
        description='List of output arguments.'
    )

    @validator('inputs')
    def check_workflow_reference(cls, v):
        input_params = v.parameters

        if input_params == None:
            return v

        ref_params = []

        for param in input_params:
            if not isinstance(param, (str, bytes)):
                continue
            if not param.value:
                continue
            if 'workflow.' in param.value:
                ref_params.append(param)
        if len(ref_params) > 0:
            params = ['{}: {}'.format(param.name, param.value)
                      for param in ref_params]
            warnings.warn(
                'Referencing workflow parameters in a template function makes the'
                ' function less reusable. Try using inputs / outputs of the function'
                ' instead and assign workflow values in flow section when calling'
                ' this function.\n\t- {}'.format('\n\t-'.join(params))
            )
        return v

    def validate_all(self):
        """Check that all the elements of the function are valid together"""
        self.check_command_referenced_values()
        self.check_output_referenced_values()


    def check_command_referenced_values(self):
        values = self.dict()
        v = values.get('command')
        # get references
        match = var_parser(v)
        if not match:
            return values
        # ensure referenced values are valid
        func_name = values.get('name')
        if 'inputs' in values and values['inputs'] != None:
            input_names = [param.get('name')
                           for param in values['inputs']['parameters']]
        else:
            input_names = []
        # check inputs
        self.validate_variable(match, func_name, input_names)
        return values


    def check_output_referenced_values(self):
        values = self.dict()
        v = values.get('outputs')

        if v == None:
            return values

        output_paths = []
        output_values = []

        if v.get('parameters') is not None:
            output_paths.extend([p['path'] for p in v['parameters']])
            output_values.extend([p['value'] for p in v['parameters']])

        if v.get('artifacts') is not None:
            output_paths.extend([p['path'] for p in v['artifacts']])
            output_paths.extend([p['source_path'] for p in v['artifacts']])

        output_paths = filter(None, output_paths)
        output_values = filter(None, output_values)

        ref_params = []
        for path in output_paths:
            if 'workflow.' in path:
                ref_params.append(path)
        if len(ref_params) > 0:
            warnings.warn(
                'Referencing workflow parameters in a template function makes the'
                ' function less reusable. Try using inputs / outputs of the function'
                ' instead and assign workflow values in flow section when calling'
                ' this function.\n\t- {}'.format('\n\t-'.join(ref_params))
            )
        # check the variables are fine
        func_name = values.get('name')
        if 'inputs' in values and values['inputs'] != None and values['inputs']['parameters'] != None:
            input_names = [param.get('name') for param in values['inputs']['parameters']]
        else:
            input_names = []

        for path in output_paths:
            match = var_parser(path)
            self.validate_variable(match, func_name, input_names)

        for value in output_values:
            match = var_parser(value)
            self.validate_variable(match, func_name, input_names)

        return values

    @staticmethod
    def validate_variable(variables, func_name, input_names):
        """Validate referenced variables.

        Referenced variables must follow x.y.z pattern and start with inputs, outputs or
        workflow (e.g. inputs.parameters.filename).

        This method is a helper that is used by other @validator classmethods.
        """
        for m in variables:
            try:
                ref, typ, name = m.split('.')
            except ValueError:
                raise ValueError(
                    '{{%s}} in %s function does not follow x.y.z pattern' % (
                        m, func_name)
                )

            if not ref in ('inputs', 'outputs', 'workflow'):
                raise ValueError(
                    'Referenced values must start with inputs, outputs or workflow'
                )
            if ref == 'workflow':
                warnings.warn(
                    '[{}]: Referencing workflow parameters in a function '
                    ' makes the function less reusable. Use inputs of the function'
                    ' instead and assign workflow values in flow section when calling'
                    ' this function. Reference: {}'.format(func_name, m)
                )
                continue

            # now ensure input references are valid
            if ref != 'inputs' or typ != 'parameters':
                continue

            assert name in input_names, \
                'Illegal output parameter name in "%s": {{%s}}\n' \
                'Valid inputs:\n\t- %s' % (func_name,
                                           m, '\n\t- '.join(input_names))
