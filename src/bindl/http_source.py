from multiprocessing.pool import ThreadPool
from pathlib import Path

from pydantic import HttpUrl

from bindl.download import DownloadJob
from bindl.github import AssetDownloadJob
from bindl.models import AssetFile, AssetInfo


def download_http_assets(
    url_map: dict[str, HttpUrl],
    *,
    download_root: Path,
) -> list[AssetFile]:
    download_root.mkdir(parents=True, exist_ok=True)
    asset_download_jobs: list[AssetDownloadJob] = []
    for name, url in url_map.items():
        url = str(url)
        asset_info = AssetInfo(data={"browser_download_url": url}, name=name)
        target_filename = download_root / name
        dj = DownloadJob(url=url, dest=target_filename, sha256_url=None)
        asset_download_jobs.append(AssetDownloadJob(asset=asset_info, download=dj))
    with ThreadPool(4) as pool:
        for _ in pool.imap_unordered(lambda adj: adj.download.run(), asset_download_jobs):
            pass
    return [AssetFile(asset=adj.asset, local_path=adj.download.dest) for adj in asset_download_jobs]
