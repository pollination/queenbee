"""Queenbee alias output types.

Use these alias outputs to create a different IO object for client side UIs.
"""

from typing import Union, List

from pydantic import constr, Field, validator

from ..common import ItemType, GenericOutput, find_dup_items, IOAliasHandler
from ..reference import FileReference, FolderReference, TaskReference


class DAGGenericOutputAlias(GenericOutput):
    """DAG generic alias output.

    In most cases, you should not be using the generic output unless you need a dynamic
    output that changes its type in different platforms because of returning different
    objects in handler.
    """
    type: constr(regex='^DAGGenericOutputAlias$') = 'DAGGenericOutputAlias'

    platform: List[str] = Field(
        ...,
        description='Name of the client platform (e.g. Grasshopper, Revit, etc). The '
        'value can be any strings as long as it has been agreed between client-side '
        'developer and author of the recipe.'
    )

    handler: List[IOAliasHandler] = Field(
        ...,
        description='List of process actions to process the input or output value.'
    )

    @validator('platform', always=True)
    def create_empty_platform_list(cls, v):
        return [] if v is None else v

    @validator('handler', always=True)
    def check_duplicate_platform_name(cls, v, values):
        v = [] if v is None else v
        languages = [h.language for h in v]
        dup_lang = find_dup_items(languages)
        if dup_lang:
            raise ValueError(
                f'Duplicate use of language(s) found in alias handlers for '
                f'{values["platform"]}: {dup_lang}. Each language can only be used once '
                'in each platform.'
            )
        return v


class DAGLinkedOutputAlias(DAGGenericOutputAlias):
    """An Alias for Linked Outputs.

    A linked output alias will be translated to an object in the UI and stay linked to
    it.
    """
    type: constr(regex='^DAGLinkedOutputAlias$') = 'DAGLinkedOutputAlias'


class DAGFileOutputAlias(DAGGenericOutputAlias):
    """DAG alias file output."""
    type: constr(regex='^DAGFileOutputAlias$') = 'DAGFileOutputAlias'

    from_: Union[TaskReference, FileReference] = Field(
        ...,
        description='Reference to a file or a task output. Task output must be file.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGFolderOutputAlias(DAGGenericOutputAlias):
    """DAG alias folder output."""
    type: constr(regex='^DAGFolderOutputAlias$') = 'DAGFolderOutputAlias'

    from_: Union[TaskReference, FolderReference] = Field(
        ...,
        description='Reference to a folder or a task output. Task output must be folder.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGPathOutputAlias(DAGGenericOutputAlias):
    """DAG alias path output."""
    type: constr(regex='^DAGPathOutputAlias$') = 'DAGPathOutputAlias'

    from_: Union[TaskReference, FileReference, FolderReference] = Field(
        ...,
        description='Reference to a file, folder or a task output. Task output must '
        'either be a file or a folder.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGStringOutputAlias(DAGFileOutputAlias):
    """DAG alias string output.

    This output loads the content from a file as a string.
    """
    type: constr(regex='^DAGStringOutputAlias$') = 'DAGStringOutputAlias'

    @property
    def is_artifact(self):
        return False


class DAGIntegerOutputAlias(DAGStringOutputAlias):
    """DAG alias integer output.

    This output loads the content from a file as an integer.
    """
    type: constr(regex='^DAGIntegerOutputAlias$') = 'DAGIntegerOutputAlias'


class DAGNumberOutputAlias(DAGStringOutputAlias):
    """DAG alias number output.

    This output loads the content from a file as a floating number.
    """
    type: constr(regex='^DAGNumberOutputAlias$') = 'DAGNumberOutputAlias'


class DAGBooleanOutputAlias(DAGStringOutputAlias):
    """DAG alias boolean output.

    This output loads the content from a file as a boolean.
    """
    type: constr(regex='^DAGBooleanOutputAlias$') = 'DAGBooleanOutputAlias'


class DAGArrayOutputAlias(DAGStringOutputAlias):
    """DAG alias array output.

    This output loads the content from a JSON file which must be a JSON Array.
    """
    type: constr(regex='^DAGArrayOutputAlias$') = 'DAGArrayOutputAlias'

    items_type: ItemType = Field(
        ItemType.String,
        description='Type of items in this array. All the items in an array must be '
        'from the same type.'
    )


class DAGJSONObjectOutputAlias(DAGStringOutputAlias):
    """DAG alias object output.

    This output loads the content from a file as a JSON object.
    """
    type: constr(regex='^DAGJSONObjectOutputAlias$') = 'DAGJSONObjectOutputAlias'


DAGAliasOutputs = Union[
    DAGGenericOutputAlias, DAGStringOutputAlias, DAGIntegerOutputAlias,
    DAGNumberOutputAlias, DAGBooleanOutputAlias, DAGFolderOutputAlias,
    DAGFileOutputAlias, DAGPathOutputAlias, DAGArrayOutputAlias,
    DAGJSONObjectOutputAlias, DAGLinkedOutputAlias
]
