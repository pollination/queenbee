"""IO handler objects."""
from typing import List, Dict

from pydantic import constr, Field, validator

from ..base.basemodel import BaseModel


class HandlerAction(BaseModel):
    """Handler action object."""

    type: constr(regex='^HandlerAction$') = 'HandlerAction'

    case: List[str] = Field(
        ...,
        description='Declare the object type (e.g. python, dotnet, string, etc.). This '
        'option allows the recipe to be flexible on handling different types of values '
        'for an input or output. For instance one can load the values from a python '
        'object or a dotnet object and directly use an input string without processing. '
        'The input can be any string as long as it is agreed upon between the UI '
        'developer and the author of the recipe.'
    )

    script: str = Field(
        None,
        description='An executable script. Use input or link name as the variable name '
        'in this script. A script can be written in multiple lines. You should not '
        'include the return statement in the script and use return field instead to '
        'clarify the return variable.',
        # example='model.write()  # model is the name of the input in handler'
    )

    return_: str = Field(
        None,
        description='Name of return variable. This is a required field if script is '
        'provided',
        alias='return'
    )

    @validator('return_', always=True)
    def validate_return(cls, v, values):
        script = values.get('script')
        if not script and v:
            raise ValueError(f'Return variable {v} is provided for an empty script.')
        if script and not v:
            raise ValueError(
                'A return variable must be provided for an action with a script.'
            )
        return v


class OutputHandler(BaseModel):
    """A handler to process output value.

    The handler is usually used to handle loading the input values for a graphical
    user interface.
    """
    type: constr(regex='^OutputHandler$') = 'OutputHandler'

    platform: List[str] = Field(
        ...,
        description='Name of the client platform (e.g. Grasshopper, Revit, etc). The '
        'value can be any strings as long as it has been agreed between client-side '
        'developer and author of the recipe.'
    )

    name: str = Field(
        None,
        description='An alternative name. If not provided the original name will be '
        'used.'
    )

    description: str = Field(
        None,
        description='An alternative description for input to be used instead of the '
        'original description.'
    )

    action: List[HandlerAction] = Field(
        ...,
        description='List of process actions to process the input or output value.'
    )


class InputHandler(OutputHandler):
    """A handler to process input value.

    The handler is usually used to handle loading the input values for a graphical
    user interface.
    """
    type: constr(regex='^InputHandler$') = 'InputHandler'

    link: str = Field(
        None,
        description='Use this field to link the input to an object using its name. Once '
        'the input is linked to the object inside the GUI it will not be '
        'available to user for modification. link and name fields should not be used '
        'together.'
    )

    spec: Dict = Field(
        None,
        description='An optional JSON Schema specification to validate the input value. '
        'If provided this spec should be used over the default spec.'
    )

    @validator('link')
    def check_link_or_name(cls, v, values):
        """Ensure either name of link has been provided."""
        name = values.get('name')
        if name and v:
            raise ValueError(
                f'InputHandler can either accept the name ({name}) or be linked to {v}.'
            )
        return v
