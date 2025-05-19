import logging
from pathlib import Path
from typing import Callable

from bindl.download import AssetDownloadJob, DownloadJob, download_json, run_asset_download_jobs
from bindl.models import AssetInfo, GitHubReleaseAssetFile, GitHubReleaseInfo

log = logging.getLogger(__name__)


def download_github_assets(
    ri: GitHubReleaseInfo,
    *,
    is_acceptable: Callable[[str], bool],
    download_root: Path,
) -> list[GitHubReleaseAssetFile]:
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
    run_asset_download_jobs(asset_download_jobs)
    return [
        GitHubReleaseAssetFile(
            release=ri,
            asset=adj.asset,
            local_path=adj.download.dest,
        )
        for adj in asset_download_jobs
    ]


def get_latest_release(project_name: str) -> GitHubReleaseInfo:
    log.info("Finding releases for %s...", project_name)
    res = download_json(f"https://api.github.com/repos/{project_name}/releases")
    latest_release = sorted(
        [r for r in res if not (r["draft"] or r["prerelease"])],
        key=lambda r: r["created_at"],
        reverse=True,
    )[0]
    ri = GitHubReleaseInfo(
        data=latest_release,
        name=latest_release["tag_name"].lstrip("v"),
        project_name=project_name.partition("/")[2],
    )
    log.info("OK – Latest release for %s: %s", project_name, ri.name)
    return ri
