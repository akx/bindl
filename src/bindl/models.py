import dataclasses
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class GitHubReleaseInfo:
    data: dict
    name: str
    project_name: str


@dataclasses.dataclass(frozen=True)
class AssetInfo:
    data: dict
    name: str


@dataclasses.dataclass(frozen=True)
class AssetFile:
    asset: AssetInfo
    local_path: Path


@dataclasses.dataclass(frozen=True)
class GitHubReleaseAssetFile(AssetFile):
    release: GitHubReleaseInfo
