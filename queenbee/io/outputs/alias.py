"""Queenbee alias output types.

Use these alias outputs to create a different IO object for client side UIs.
"""

from typing import Union, List, Literal

from pydantic import Field, field_validator, ValidationInfo

from ..common import ItemType, GenericOutput, find_dup_items, IOAliasHandler
from ..reference import FileReference, FolderReference, TaskReference


class DAGGenericOutputAlias(GenericOutput):
    """DAG generic alias output.

    In most cases, you should not be using the generic output unless you need a dynamic
    output that changes its type in different platforms because of returning different
    objects in handler.
    """
    type: Literal['DAGGenericOutputAlias'] = 'DAGGenericOutputAlias'

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

    @field_validator('platform', mode='before')
    @classmethod
    def create_empty_platform_list(cls, v: List[str]) -> List[str]:
        return [] if v is None else v

    @field_validator('handler', mode='before')
    @classmethod
    def check_duplicate_platform_name(cls, v: List[IOAliasHandler], info: ValidationInfo) -> List[IOAliasHandler]:
        v = [] if v is None else v
        languages = [h.language for h in v]
        dup_lang = find_dup_items(languages)
        if dup_lang:
            raise ValueError(
                f'Duplicate use of language(s) found in alias handlers for '
                f'{info.data.get("platform", "unknown")}: {dup_lang}. Each language can only be used once '
                'in each platform.'
            )
        return v


class DAGLinkedOutputAlias(DAGGenericOutputAlias):
    """An Alias for Linked Outputs.

    A linked output alias will be translated to an object in the UI and stay linked to
    it.
    """
    type: Literal['DAGLinkedOutputAlias'] = 'DAGLinkedOutputAlias'


class _DAGArtifactOutputAlias(DAGGenericOutputAlias):
    """Base class for DAG artifact output aliases.

    This class add a required input. By default all artifact outputs are required.
    """
    required: bool = Field(
        True,
        description='A boolean to indicate if an artifact output is required. A False '
        'value makes the artifact optional.'
    )

    @property
    def is_optional(self):
        return not self.required


class DAGFileOutputAlias(_DAGArtifactOutputAlias):
    """DAG alias file output."""
    type: Literal['DAGFileOutputAlias'] = 'DAGFileOutputAlias'

    from_: Union[TaskReference, FileReference] = Field(
        ...,
        description='Reference to a file or a task output. Task output must be file.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGFolderOutputAlias(_DAGArtifactOutputAlias):
    """DAG alias folder output."""
    type: Literal['DAGFolderOutputAlias'] = 'DAGFolderOutputAlias'

    from_: Union[TaskReference, FolderReference] = Field(
        ...,
        description='Reference to a folder or a task output. Task output must be folder.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGPathOutputAlias(_DAGArtifactOutputAlias):
    """DAG alias path output."""
    type: Literal['DAGPathOutputAlias'] = 'DAGPathOutputAlias'

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
    type: Literal['DAGStringOutputAlias'] = 'DAGStringOutputAlias'

    @property
    def is_artifact(self):
        return False


class DAGIntegerOutputAlias(DAGStringOutputAlias):
    """DAG alias integer output.

    This output loads the content from a file as an integer.
    """
    type: Literal['DAGIntegerOutputAlias'] = 'DAGIntegerOutputAlias'


class DAGNumberOutputAlias(DAGStringOutputAlias):
    """DAG alias number output.

    This output loads the content from a file as a floating number.
    """
    type: Literal['DAGNumberOutputAlias'] = 'DAGNumberOutputAlias'


class DAGBooleanOutputAlias(DAGStringOutputAlias):
    """DAG alias boolean output.

    This output loads the content from a file as a boolean.
    """
    type: Literal['DAGBooleanOutputAlias'] = 'DAGBooleanOutputAlias'


class DAGArrayOutputAlias(DAGStringOutputAlias):
    """DAG alias array output.

    This output loads the content from a JSON file which must be a JSON Array.
    """
    type: Literal['DAGArrayOutputAlias'] = 'DAGArrayOutputAlias'

    items_type: ItemType = Field(
        ItemType.String,
        description='Type of items in this array. All the items in an array must be '
        'from the same type.'
    )


class DAGJSONObjectOutputAlias(DAGStringOutputAlias):
    """DAG alias object output.

    This output loads the content from a file as a JSON object.
    """
    type: Literal['DAGJSONObjectOutputAlias'] = 'DAGJSONObjectOutputAlias'


DAGAliasOutputs = Union[
    DAGGenericOutputAlias, DAGStringOutputAlias, DAGIntegerOutputAlias,
    DAGNumberOutputAlias, DAGBooleanOutputAlias, DAGFolderOutputAlias,
    DAGFileOutputAlias, DAGPathOutputAlias, DAGArrayOutputAlias,
    DAGJSONObjectOutputAlias, DAGLinkedOutputAlias
]
