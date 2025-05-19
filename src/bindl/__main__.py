import argparse
from pathlib import Path

from bindl.config import Config
from bindl.config.source_config import GitHubSourceConfig, HTTPSourceConfig
from bindl.helpers import make_any_match
from bindl.lib import recompress_files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec_toml")
    ap.add_argument("-o", "--output-dir", required=True)
    ap.add_argument("--temp-dir", default=".temp")
    args = ap.parse_args()
    cfg = Config.from_toml_path(Path(args.spec_toml))

    temp_root = Path(args.temp_dir) / cfg.temp_dir_identifier
    if isinstance(cfg.source, GitHubSourceConfig):
        from bindl.github import download_github_assets, get_latest_release

        release = get_latest_release(cfg.source.github)
        release_name = release.name
        release_asset_files = download_github_assets(
            release,
            is_acceptable=make_any_match(cfg.source.included_release_files),
            download_root=temp_root / "download",
        )
    elif isinstance(cfg.source, HTTPSourceConfig):
        from bindl.http_source import download_http_assets

        release_name = cfg.source.release_name

        release_asset_files = download_http_assets(
            cfg.source.http,
            download_root=temp_root / "download" / release_name,
        )
    else:
        raise ValueError("No source specified.")
    extract_root = temp_root / "extract" / release_name
    recompress_files(
        files=release_asset_files,
        extract_root=extract_root,
        output_root=Path(args.output_dir),
        target_config=cfg.target,
        is_acceptable_tarball_member_name=make_any_match(cfg.source.included_tarball_member_names),
        release_name=release_name,
    )


if __name__ == "__main__":
    main()
