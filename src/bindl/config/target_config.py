from __future__ import annotations

from pathlib import Path
from typing import Callable

from pydantic import BaseModel, Field

from bindl.helpers import FilteringFormatter
from bindl.models import AssetInfo


class TargetConfig(BaseModel):
    gz_pattern: str = Field(alias="gz-pattern")

    def make_target_gz_name(
        self,
        *,
        asset: AssetInfo,
        asset_name_cleaner: Callable[[str], str],
        name: str,
        output_root: Path,
        release_name: str,
    ) -> Path:
        fmt = FilteringFormatter()
        ns = {
            "asset_name": asset.name,
            "asset_name_cleaned": asset_name_cleaner(asset.name),
            "name": name,
            "release_name": release_name,
        }
        return output_root.joinpath(Path(fmt.vformat(self.gz_pattern, (), ns)))
