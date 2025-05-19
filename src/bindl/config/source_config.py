from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BaseModel, Field, HttpUrl


class BaseSourceConfig(BaseModel):
    included_tarball_member_names: Annotated[
        list[re.Pattern],
        Field(alias="included-tarball-member-names", default_factory=list),
    ]


class GitHubSourceConfig(BaseSourceConfig):
    github: Annotated[str | None, Field(pattern=r"^.+/.+$")] = None
    included_release_files: Annotated[
        list[re.Pattern],
        Field(alias="included-release-files", default_factory=list),
    ]


class HTTPSourceConfig(BaseSourceConfig):
    release_name: Annotated[str, Field(default="current")]
    http: dict[str, HttpUrl] | None = None


def get_source_config_type(v: Any) -> str:
    if isinstance(v, dict):
        if "github" in v:
            return "github"
        elif "http" in v:
            return "http"
    raise ValueError("Invalid source config type.")
