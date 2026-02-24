"""Queenbee output types for a DAG."""

from typing import Union, List

from pydantic import Field

from ..common import ItemType, FromOutput
from .alias import DAGAliasOutputs
from ..reference import FileReference, FolderReference, TaskReference
from typing import Literal


class DAGGenericOutput(FromOutput):
    """DAG generic output.

    In most cases, you should not be using the generic output unless you need a dynamic
    output that changes its type in different platforms because of returning different
    objects in handler.
    """
    type: Literal['DAGGenericOutput'] = 'DAGGenericOutput'

    alias: List[DAGAliasOutputs] = Field(
        default_factory=list,
        description='A list of additional processes for loading this output on '
        'different platforms.'
    )

class _DAGArtifactOutput(DAGGenericOutput):
    """Base class for DAG artifact outputs.

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


class DAGFileOutput(_DAGArtifactOutput):
    """DAG file output."""
    type: Literal['DAGFileOutput'] = 'DAGFileOutput'

    from_: Union[TaskReference, FileReference] = Field(
        ...,
        description='Reference to a file or a task output. Task output must be file.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGFolderOutput(_DAGArtifactOutput):
    """DAG folder output."""
    type: Literal['DAGFolderOutput'] = 'DAGFolderOutput'

    from_: Union[TaskReference, FolderReference] = Field(
        ...,
        description='Reference to a folder or a task output. Task output must be folder.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGPathOutput(_DAGArtifactOutput):
    """DAG path output."""
    type: Literal['DAGPathOutput'] = 'DAGPathOutput'

    from_: Union[TaskReference, FileReference, FolderReference] = Field(
        ...,
        description='Reference to a file, folder or a task output. Task output must '
        'either be a file or a folder.',
        alias='from'
    )

    @property
    def is_artifact(self):
        return True


class DAGStringOutput(DAGFileOutput):
    """DAG string output.

    This output loads the content from a file as a string.
    """
    type: Literal['DAGStringOutput'] = 'DAGStringOutput'

    @property
    def is_artifact(self):
        return False


class DAGIntegerOutput(DAGStringOutput):
    """DAG integer output.

    This output loads the content from a file as an integer.
    """
    type: Literal['DAGIntegerOutput'] = 'DAGIntegerOutput'


class DAGNumberOutput(DAGStringOutput):
    """DAG number output.

    This output loads the content from a file as a floating number.
    """
    type: Literal['DAGNumberOutput'] = 'DAGNumberOutput'


class DAGBooleanOutput(DAGStringOutput):
    """DAG boolean output.

    This output loads the content from a file as a boolean.
    """
    type: Literal['DAGBooleanOutput'] = 'DAGBooleanOutput'


class DAGArrayOutput(DAGStringOutput):
    """DAG array output.

    This output loads the content from a JSON file which must be a JSON Array.
    """
    type: Literal['DAGArrayOutput'] = 'DAGArrayOutput'

    items_type: ItemType = Field(
        ItemType.String,
        description='Type of items in this array. All the items in an array must be '
        'from the same type.'
    )


class DAGJSONObjectOutput(DAGStringOutput):
    """DAG object output.

    This output loads the content from a file as a JSON object.
    """
    type: Literal['DAGJSONObjectOutput'] = 'DAGJSONObjectOutput'


DAGOutputs = Union[
    DAGGenericOutput, DAGStringOutput, DAGIntegerOutput, DAGNumberOutput,
    DAGBooleanOutput, DAGFolderOutput, DAGFileOutput, DAGPathOutput, DAGArrayOutput,
    DAGJSONObjectOutput
]
