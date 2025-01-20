import dataclasses
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class ReleaseInfo:
    data: dict
    name: str
    project_name: str


@dataclasses.dataclass(frozen=True)
class AssetInfo:
    data: dict
    name: str


@dataclasses.dataclass(frozen=True)
class ReleaseAssetFile:
    release: ReleaseInfo
    asset: AssetInfo
    local_path: Path
