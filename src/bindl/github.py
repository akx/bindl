import dataclasses
import logging
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import Callable

from bindl.download import DownloadJob, download_json
from bindl.models import AssetInfo, ReleaseAssetFile, ReleaseInfo

log = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class AssetDownloadJob:
    asset: AssetInfo
    download: DownloadJob


def download_assets(
    ri: ReleaseInfo,
    *,
    is_acceptable: Callable[[str], bool],
    download_root: Path,
) -> list[ReleaseAssetFile]:
    download_root = download_root / ri.name
    download_root.mkdir(parents=True, exist_ok=True)
    asset_download_jobs: list[AssetDownloadJob] = []
    assets_by_name = {asset["name"]: asset for asset in ri.data["assets"]}
    for asset in ri.data["assets"]:
        url = asset["browser_download_url"]
        name = asset["name"]
        asset_info = AssetInfo(data=asset, name=name)
        if is_acceptable(name):
            sha256_asset = assets_by_name.get(f"{name}.sha256")
            target_filename = download_root / name
            sha256_url = sha256_asset["browser_download_url"] if sha256_asset else None
            dj = DownloadJob(url=url, dest=target_filename, sha256_url=sha256_url)
            asset_download_jobs.append(AssetDownloadJob(asset=asset_info, download=dj))
    with ThreadPool(4) as pool:
        for _ in pool.imap_unordered(lambda adj: adj.download.run(), asset_download_jobs):
            pass
    return [
        ReleaseAssetFile(
            release=ri,
            asset=adj.asset,
            local_path=adj.download.dest,
        )
        for adj in asset_download_jobs
    ]


def get_latest_release(project_name: str) -> ReleaseInfo:
    print(f"*** Finding releases for {project_name}...")
    res = download_json(f"https://api.github.com/repos/{project_name}/releases")
    latest_release = sorted(
        [r for r in res if not (r["draft"] or r["prerelease"])],
        key=lambda r: r["created_at"],
        reverse=True,
    )[0]
    ri = ReleaseInfo(
        data=latest_release,
        name=latest_release["tag_name"].lstrip("v"),
        project_name=project_name.partition("/")[2],
    )
    print(" -> Latest release:", ri.name)
    return ri
