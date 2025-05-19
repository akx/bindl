from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Discriminator, Tag

from bindl.config.source_config import GitHubSourceConfig, HTTPSourceConfig, get_source_config_type
from bindl.config.target_config import TargetConfig

try:
    import tomllib
except ImportError:
    import tomli as tomllib


class Config(BaseModel):
    config_path: Path | None = None
    source: Annotated[
        (Annotated[GitHubSourceConfig, Tag("github")] | Annotated[HTTPSourceConfig, Tag("http")]),
        Discriminator(get_source_config_type),
    ]
    target: TargetConfig

    @classmethod
    def from_toml_path(cls, p: Path) -> Config:
        with p.open("rb") as f:
            return Config.model_validate(
                {
                    **tomllib.load(f),
                    "config_path": p,
                },
            )

    @cached_property
    def temp_dir_identifier(self) -> str:
        if isinstance(self.source, GitHubSourceConfig):
            return self.source.github.replace("/", "__")
        return self.config_path.stem
