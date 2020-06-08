import os
import json
from pathlib import Path

from pydantic import Field
from ..base.basemodel import BaseModel
from ..config import Config as QueenbeeConfig

DEFAULT_CONFIG_DIR = os.path.join(Path.home(), '.queenbee')
DEFAULT_CONFIG_PATH = os.path.join(DEFAULT_CONFIG_DIR, 'config.yml')

def init_config():

    try:
        return QueenbeeConfig.from_file(filepath=DEFAULT_CONFIG_PATH)
    except Exception as error:
        print(error)
        pass

    os.makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)

    config = QueenbeeConfig()

    config.to_yaml(filepath=DEFAULT_CONFIG_PATH)

    return config

class Context(BaseModel):

    config_directory: str = Field(
        DEFAULT_CONFIG_DIR,
    )

    config_path: str = Field(
        DEFAULT_CONFIG_PATH,
    )

    config: QueenbeeConfig = Field(
        default_factory=init_config,
    )

    def refresh_tokens(self):
        self.config.refresh_tokens()
        self.config.to_yaml(filepath=self.config_path)

    def write_config(self):
        self.config.to_yaml(filepath=self.config_path)
