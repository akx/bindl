from __future__ import annotations

import atexit
import dataclasses
import hashlib
import logging
from multiprocessing.pool import ThreadPool
from pathlib import Path

import httpx

from bindl.models import AssetInfo

log = logging.getLogger(__name__)

client = httpx.Client()
atexit.register(client.close)


def download_binary(url) -> bytes:
    resp = client.get(url, follow_redirects=True)
    resp.raise_for_status()
    return resp.content


def download_text(url) -> str:
    resp = client.get(url, follow_redirects=True)
    resp.raise_for_status()
    return resp.content.decode("utf-8")


def download_json(url):
    resp = client.get(url)
    resp.raise_for_status()
    return resp.json()


@dataclasses.dataclass(frozen=True)
class DownloadJob:
    url: str
    dest: Path
    sha256_url: str | None = None

    def run(self):
        if self.is_complete():
            log.info("Already downloaded: %s", self.dest)
            return
        log.info("Downloading %s to %s", self.url, self.dest)
        bs = download_binary(self.url)
        self.dest.write_bytes(bs)
        if not self.is_complete():
            raise RuntimeError("Failed to download file")

    def is_complete(self) -> bool:
        if not self.dest.is_file():
            return False
        if self.sha256_url:
            expected_sha256 = download_text(self.sha256_url).split(None, 1)[0]
            real_sha256 = hashlib.sha256(self.dest.read_bytes()).hexdigest()
            if expected_sha256 != real_sha256:
                log.warning(
                    f"SHA256 mismatch for {self.dest}: {expected_sha256[:8]} != {real_sha256[:8]}",
                )
                return False
        return True


@dataclasses.dataclass(frozen=True)
class AssetDownloadJob:
    asset: AssetInfo
    download: DownloadJob


def run_asset_download_jobs(jobs: list[AssetDownloadJob]) -> None:
    log.info("Running %d downloads...", len(jobs))
    with ThreadPool(4) as pool:
        for _ in pool.imap_unordered(lambda adj: adj.download.run(), jobs):
            pass
