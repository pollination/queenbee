"""Queenbee utility functions."""
import hashlib
from typing import List, Dict, Any, Optional

import yaml
from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, field_validator, ValidationError

from .parser import parse_file
from .variable import get_ref_variable


# set up yaml.dump to keep the order of the input dictionary
# from https://stackoverflow.com/a/31609484/4394669
def _keep_name_order_in_yaml():
    represent_dict_order = \
        lambda self, data:  self.represent_mapping(
            'tag:yaml.org,2002:map', data.items())
    yaml.add_representer(dict, represent_dict_order)


_keep_name_order_in_yaml()


class BaseModelNoType(PydanticBaseModel):
    """BaseModel with functionality to return the object as a yaml string.

    This BaseModel does not enforce adding a type. This is useful for subclasses in
    extensions.
    """

    def yaml(self, exclude_defaults: bool = False, exclude_none: bool = False, **kwargs):
        """Get a YAML string from the model

        Keyword Arguments:
            exclude_defaults {bool} -- Whether to exclude fields that are set to their
            default values. (default: {False})

        Returns:
            str -- A yaml string representing the model
        """
        data = self.model_dump(
            mode='json', by_alias=True, exclude_defaults=exclude_defaults, exclude_none=exclude_none, **kwargs
        )
        return yaml.dump(
            data,
            default_flow_style=False
        )

    def to_dict(self, exclude_defaults: bool = False, by_alias: bool = True, exclude_none: bool = False, **kwargs):
        """Get a dictionary from the model

        Keyword Arguments:
            exclude_defaults {bool} -- Whether to exclude fields that are set to their
                default values.
                (default: {False})
            by_alias {bool} -- Boolean toggle to use attribute alias or attribute names
                as key (default: {True})

        Returns:
            dict -- A python dictionary representing the model
        """
        return self.model_dump(
            mode='json', by_alias=by_alias, exclude_defaults=exclude_defaults, exclude_none=exclude_none, **kwargs
        )

    def to_json(self, filepath: str, indent: int = None, **kwargs):
        """Write a JSON file of the model

        Arguments:
            filepath {str} -- Path to the file to be written

        Keyword Arguments:
            indent {int} -- indent amount (default: {None})
        """
        with open(filepath, 'w') as file:
            file.write(self.model_dump_json(by_alias=True, indent=indent, exclude_none=True, **kwargs))

    def to_yaml(self, filepath: str, exclude_defaults: bool = False, exclude_none: bool = True, **kwargs):
        """Write a YAML file of the model

        Arguments:
            filepath {str} -- Path to the file to be written

        Keyword Arguments:
            exclude_defaults {bool} -- Whether to exclude fields that are set to their
            default values. (default: {False})
        """
        content = self.yaml(exclude_defaults=exclude_defaults, exclude_none=exclude_none, **kwargs)

        with open(filepath, 'w') as out_file:
            out_file.write(content)

    @classmethod
    def from_file(cls, filepath):
        """Create a model from a file

        Arguments:
            filepath {str} -- Path to the file to read (can be JSON or YAML)

        Returns:
            cls -- An instance of the pydantic class
        """
        data = parse_file(filepath)
        try:
            return cls.model_validate(data)
        except ValidationError as e:
            raise ValueError(e) from e

    def __repr__(self):
        return self.yaml()

    @property
    def __hash__(self):
        """Return a model hash

        Returns:
            str -- A hash/digest of the model
        """
        return hashlib.sha256(
            self.model_dump_json(by_alias=True, exclude_none=True).encode('utf-8')
        ).hexdigest()

    def _referenced_values(self, var_names: List[str]) -> Dict[str, List[str]]:
        """Get all referenced values specified by var name

        Arguments:
            var_names {List[str]} -- List of class attribute names to check for
                referenced values

        Returns:
            Dict[str, List[str]] -- A dictionary where each key corresponds to a class
                attribute indexing a list of referenced values
        """
        ref_values = {}

        for name in var_names:
            value = getattr(self, name, None)

            if isinstance(value, str):
                ref_var = get_ref_variable(value)

                if ref_var != []:
                    ref_values[name] = ref_var

        return ref_values


class BaseModel(BaseModelNoType):
    """BaseModel with functionality to return the object as a yaml string."""

    type: str = Field(default='BaseModel', pattern='^BaseModel$')

    annotations: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description='An optional dictionary to add annotations to inputs. These '
        'annotations will be used by the client side libraries.',
        validate_default=True
    )

    @field_validator('annotations', mode='before')
    @classmethod
    def convert_none_to_empty_dict(cls, v):
        return v if v is not None else {}

    @field_validator('type')
    @classmethod
    def ensure_type_match(cls, v: str) -> str:
        name = cls.__name__
        if name != v:
            raise ValueError(
                f'The value for "type" ({v}) must be the same as class name ({name}). '
                'In most cases, this is the result of not adding the type field to the '
                f'Pydantic object. In this case: {name}'
            )
        return v
