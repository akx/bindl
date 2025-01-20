import atexit
import dataclasses
import hashlib
import logging
from pathlib import Path

import httpx

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
            print(f"Already have: {self.dest}")
            return
        print(f"Downloading {self.url} to {self.dest}")
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
