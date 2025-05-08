# bindl

A tool for downloading and repackaging binary releases from GitHub.

## Overview

Bindl simplifies the process of maintaining mirrors of binary releases from GitHub projects. It:

1. Fetches the latest release of a specified GitHub repository
2. Downloads selected assets based on configurable patterns
3. Extracts specific files from tarballs
4. Recompresses them with [zopfli](https://github.com/google/zopfli) for optimal compression
5. Organizes them in a customizable directory structure

This directory structure could then be synchronized to remote storage.

## Requirements

- Python 3.8+
- zopfli command-line utility

## Usage

```bash
bindl configs/uv.toml -o out/
```

## Configuration

Bindl uses TOML files to specify what to download and how to organize the output.
Here's an example (in fact, `examples/uv.toml`):

```toml
[source]
github = "astral-sh/uv"
included-release-files = [
    ".*darwin.*tar.gz$",
    ".*(x86_64|aarch64).*linux.*gnu.*tar.gz$",
]
included-tarball-member-names = [
    "^.+/uv(x)?$",
]

[target]
gz-pattern = "{release_name}/{asset_name_cleaned|basename|strip_ext}/{name|basename}.gz"
```

### Configuration Options

#### `[source]` Section

- `github`: GitHub repository in format `owner/repo`
- `included-release-files`: List of regex patterns to match release assets to download
- `included-tarball-member-names`: List of regex patterns to match files to extract from tarballs

#### `[target]` Section

- `gz-pattern`: Pattern for final output file paths, supporting the following variables:
  - `{release_name}`: Release version
  - `{asset_name}`: Original asset filename
  - `{asset_name_cleaned}`: Asset name with project name and version prefixes removed
  - `{name}`: Original file path within the tarball

  Filters (applied with `|`):
  - `basename`: Extract basename of a path
  - `strip_ext`: Remove file extension
  - `strip_tar`: Remove .tar extension

## License

MIT
