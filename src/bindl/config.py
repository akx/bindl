from __future__ import annotations

import re
from pathlib import Path

from pydantic import BaseModel, Field

from bindl.helpers import FilteringFormatter
from bindl.models import AssetInfo, GitHubReleaseInfo

try:
    import tomllib
except ImportError:
    import tomli as tomllib


class SourceConfig(BaseModel):
    github: str = Field(pattern=r"^.+/.+$")
    included_release_files: list[re.Pattern] = Field(alias="included-release-files")
    included_tarball_member_names: list[re.Pattern] = Field(alias="included-tarball-member-names")


def clean_asset_name(name: str, release: GitHubReleaseInfo) -> str:
    name = name.removeprefix(f"{release.project_name}-")
    name = name.removeprefix(f"{release.project_name}_")
    name = name.removeprefix(f"{release.name}-")
    name = name.removeprefix(f"{release.name}_")
    return name


class TargetConfig(BaseModel):
    gz_pattern: str = Field(alias="gz-pattern")

    def make_target_gz_name(
        self,
        release: GitHubReleaseInfo,
        asset: AssetInfo,
        output_root: Path,
        name: str,
    ) -> Path:
        fmt = FilteringFormatter()
        ns = {
            "asset_name": asset.name,
            "asset_name_cleaned": clean_asset_name(asset.name, release),
            "name": name,
            "release_name": release.name,
        }
        return output_root.joinpath(Path(fmt.vformat(self.gz_pattern, (), ns)))


class Config(BaseModel):
    source: SourceConfig
    target: TargetConfig

    @classmethod
    def from_toml_path(cls, p: Path) -> Config:
        with p.open("rb") as f:
            return Config.model_validate(tomllib.load(f))
