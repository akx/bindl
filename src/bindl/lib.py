from __future__ import annotations

import dataclasses
import gzip
import logging
import subprocess
import tarfile
from functools import partial
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import Callable, Iterable

from bindl.config.target_config import TargetConfig
from bindl.models import AssetFile, GitHubReleaseAssetFile, GitHubReleaseInfo

log = logging.getLogger(__name__)


def zopfli_and_remove_file(source_path: Path, dest_path: Path):
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    compressed_bytes = subprocess.check_output(
        ["zopfli", "--gzip", "-c", str(source_path)],
    )
    dest_path.write_bytes(compressed_bytes)
    source_size = source_path.stat().st_size
    dest_size = dest_path.stat().st_size
    log.info("Compressed %s from %s to %s", source_path, source_size, dest_size)
    assert gzip.decompress(dest_path.read_bytes()) == source_path.read_bytes()
    source_path.unlink()


def recompress_files(
    files: list[AssetFile],
    *,
    extract_root: Path,
    output_root: Path,
    target_config: TargetConfig,
    is_acceptable_tarball_member_name: Callable[[str], bool],
    release_name: str,
):
    log.info("Extracting files from %d tarballs...", len(files))
    with ThreadPool() as pool:
        reco_jobs = []
        for res in pool.imap_unordered(
            lambda raf: extract_to_temp(
                raf,
                temp_dir=extract_root,
                output_root=output_root,
                target_config=target_config,
                is_acceptable_tarball_member_name=is_acceptable_tarball_member_name,
                release_name=release_name,
            ),
            files,
        ):
            reco_jobs.extend(res)

        if not reco_jobs:
            raise ValueError(
                "No files to recompress. This may mean your tarball regexp config is wrong.",
            )

        target_filenames = set(ct.target_filename for ct in reco_jobs)
        if len(target_filenames) != len(reco_jobs):
            raise ValueError(f"Duplicate target filenames: {target_filenames}")

        if all(ct.is_complete() for ct in reco_jobs):
            log.info("All files already recompressed.")
            return

        log.info("Recompressing %d files with zopfli...", len(reco_jobs))
        for _ in pool.imap_unordered(
            lambda job: zopfli_and_remove_file(job.extract_filename, job.target_filename),
            reco_jobs,
        ):
            pass


@dataclasses.dataclass(frozen=True)
class RecompressJob:
    extract_filename: Path
    target_filename: Path

    def is_complete(self) -> bool:
        return self.target_filename.is_file()


def extract_to_temp(
    af: AssetFile,
    *,
    temp_dir: Path,
    output_root: Path,
    is_acceptable_tarball_member_name: Callable[[str], bool],
    target_config: TargetConfig,
    release_name: str,
) -> Iterable[RecompressJob]:
    tarball_file = af.local_path
    if not tarball_file.name.endswith((".tar", ".tar.gz")):
        raise ValueError(f"Unexpected tarball filename: {tarball_file.name}")
    with tarfile.open(tarball_file) as tf:
        for name in tf.getnames():
            if not is_acceptable_tarball_member_name(name):
                continue
            if isinstance(af, GitHubReleaseAssetFile):
                asset_name_cleaner = partial(clean_asset_name, release=af.release)
            else:
                asset_name_cleaner = lambda x: x  # noqa: E731
            target_filename = target_config.make_target_gz_name(
                asset=af.asset,
                asset_name_cleaner=asset_name_cleaner,
                name=name,
                output_root=output_root,
                release_name=release_name,
            )
            extract_filename = temp_dir / release_name / af.asset.name / name
            if not extract_filename.is_file():
                extract_filename.parent.mkdir(parents=True, exist_ok=True)
                extract_filename.write_bytes(tf.extractfile(name).read())
                log.info("Extracted %s to %s", name, extract_filename)
            yield RecompressJob(
                extract_filename=extract_filename,
                target_filename=target_filename,
            )


def clean_asset_name(name: str, release: GitHubReleaseInfo) -> str:
    name = name.removeprefix(f"{release.project_name}-")
    name = name.removeprefix(f"{release.project_name}_")
    name = name.removeprefix(f"{release.name}-")
    name = name.removeprefix(f"{release.name}_")
    return name
