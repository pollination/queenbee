"""Queenbee input and output types.

The types and their properties are taken directly from the JSON schema definition and has
been modified to be used for Queenbee.
"""

from pydantic import constr, Field
from typing import Dict, Union, List, Any
from .basemodel import BaseModel
import re


class BaseInput(BaseModel):
    """Base class for all input types."""

    name: str = Field(
        ...,
        description='Name is the input name.'
    )

    description: str = Field(
        None,
        description='Optional description for input.'
    )

    required: bool = Field(
        False,
        description='Whether this value must be specified.'
    )

    enum: List[Any] = Field(
        None, description='An optional list for valid values.'
    )

    def validate(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        if self.enum:
            assert value in self.enum, \
                f'Invalid input value: {value}. Valid values are: f{self.enum}.'


class StringInput(BaseInput):
    """A String input."""
    type: constr(regex='^string$') = 'string'
    default: str = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )
    min_length: int = Field(None, description='Minimum length of the screen.')
    max_length: int = Field(None, description='Maximum length of the string.')
    pattern: str = Field(
        None, descritpion='A pattern to restrict a string to a particular regular '
        'expression.')

    def validate(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        value = str(value)
        super(self).validate(value)
        if self.min_length:
            assert len(value) >= len(self.min_length), \
                f'Invalid input value: {value}. ' \
                f'Minimum input length should be larger than {self.min_value}.'
        if self.max_length:
            assert len(value) <= len(self.max_length), \
                f'Invalid input value: {value}. ' \
                f'Maximum input length should be smaller than {self.max_value}.'
        if self.pattern:
            assert re.match(self.pattern, value), \
                f'Invalid input value: {value}. ' \
                f'Input value should match {self.pattern}.'
        return value


class _Numeric(BaseInput):
    minimum: float = Field(None, description='Minimum value.')
    maximum: float = Field(None, description='Maximum value.')
    exclusive_minimum: bool = Field(
        False, description='Boolean to indicate if minimum value itself is not'
        ' included.'
    )
    exclusive_maximum: bool = Field(
        False, description='Boolean to indicate if maximum value itself is not'
        ' included.'
    )

    def validate(self, value):
        """Validate an input value against specification.

        Use this for validating workflow inputs against a recipe.
        """
        if self.__class__.__name__.startswith('Integer'):
            value = int(value)
        else:
            value = float(value)

        super(self).validate(value)

        if self.minimum:
            if self.exclusive_minimum:
                assert value > len(self.minimum), \
                    f'Invalid input value: {value}. ' \
                    f'Input should be larger than {self.minimum}.'
            else:
                assert value >= self.minimum, \
                    f'Invalid input value: {value}. ' \
                    f'Input should be larger or equal to {self.minimum}.'
        if self.maximum:
            if self.exclusive_maximum:
                assert value < self.maximum, \
                    f'Invalid input value: {value}. ' \
                    f'Input should be smaller than {self.maximum}.'
            else:
                assert value <= self.maximum, \
                    f'Invalid input value: {value}. ' \
                    f'Input should be smaller or equal to {self.maximum}.'

        return value


class IntegerInput(_Numeric):
    """An integer input."""
    type: constr(regex='^integer$') = 'integer'
    default: int = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )


class NumberInput(_Numeric):
    """A number input."""
    type: constr(regex='^number$') = 'number'
    default: float = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )


class ObjectInput(BaseInput):
    """An object parameter.

    In Python an object is a dictionary.
    """
    type: constr(regex='^object$') = 'object'
    default: Dict[str, VALID_OBJECT_VALUE_TYPES] = Field(
        None,
        description='Default value to use for an input if a value was not supplied.'
    )
    properties: Dict[str, VALID_OBJECT_VALUE_TYPES] = Field(
        ..., description='The properties (key-value pairs) on an object are defined'
        ' using the properties keyword. The value of properties is an object, where'
        ' each key is the name of a property and each value is an input type used to'
        ' validate that property.'
    )
    additional_properties: bool = Field(
        False, 'A boolean to wheathear accept additional keys in properties.'
    )
    required: List[str] = Field(None, 'An optional list of required keys.')


class ArrayInput(BaseInput):
    """http://json-schema.org/understanding-json-schema/reference/array.html"""
    type: constr(regex='^object$') = 'object'
    items: List[VALID_OBJECT_VALUE_TYPES]
    min_items: int = Field(None)
    max_items: int = Field(
        None, description='The length of the array can be specified using the min_items'
        ' and max_items'
    )
    unique_items: bool = Field(
        False, description='A schema can ensure that each of the items in an array is'
        ' unique.')


class BooleanInput(BaseInput):
    """The boolean type matches only two special values: true and false. Note that values that evaluate to true or false, such as 1 and 0, are not accepted by the schema."""
    pass

class FileInput(BaseInput):
    path: str = Field(..., description='Path to file')
    pass

class FolderInput(BaseInput):
    pass


VALID_OBJECT_VALUE_TYPES = Union[
    StringInput, IntegerInput, NumberInput, ObjectInput, ArrayInput
]

ObjectInput.update_forward_refs()
ArrayInput.update_forward_refs()
