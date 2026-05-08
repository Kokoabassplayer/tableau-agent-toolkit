#!/usr/bin/env python
"""Sync Tableau document schemas from upstream tableau-document-schemas repository.

Downloads XSD files from the official tableau/tableau-document-schemas GitHub
repository and writes them to third_party/tableau_document_schemas/schemas/.
Uses urllib.request for downloads (no external dependencies).
"""

import argparse
import urllib.request
from pathlib import Path

UPSTREAM_BASE_URL = (
    "https://raw.githubusercontent.com/tableau/tableau-document-schemas/main/schemas/"
)
TARGET_DIR = Path(__file__).parent.parent / "third_party" / "tableau_document_schemas" / "schemas"
DEFAULT_VERSIONS = ["2026_1"]


def sync_version(version: str) -> list[Path]:
    """Download XSD files for a given Tableau version.

    Args:
        version: Version directory name (e.g., '2026_1').

    Returns:
        List of paths to downloaded files.
    """
    target_version_dir = TARGET_DIR / version
    target_version_dir.mkdir(parents=True, exist_ok=True)

    downloaded: list[Path] = []

    # Map version directory to the specific XSD filename
    # e.g., 2026_1 -> twb_2026.1.0.xsd
    version_parts = version.replace("_", ".").split(".")
    major = version_parts[0]  # e.g., "2026"
    minor = version_parts[1] if len(version_parts) > 1 else "1"
    xsd_filename = f"twb_{major}.{minor}.0.xsd"

    source_url = f"{UPSTREAM_BASE_URL}{version}/{xsd_filename}"
    target_path = target_version_dir / xsd_filename

    try:
        urllib.request.urlretrieve(source_url, str(target_path))
        downloaded.append(target_path)
    except Exception as e:
        print(f"Warning: Failed to download {xsd_filename}: {e}")

    return downloaded


def main() -> None:
    """Entry point for sync_tableau_schemas script."""
    parser = argparse.ArgumentParser(
        description="Sync Tableau XSD schemas from upstream tableau-document-schemas repository.",
    )
    parser.add_argument(
        "--versions",
        nargs="*",
        default=DEFAULT_VERSIONS,
        help=f"Versions to sync (default: {DEFAULT_VERSIONS}). Example: 2026_1 2025_4",
    )
    args = parser.parse_args()

    all_downloaded: list[Path] = []
    for version in args.versions:
        files = sync_version(version)
        all_downloaded.extend(files)

    # Update README with sync date
    readme_path = TARGET_DIR.parent / "README.md"
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    readme_content = (
        "# Vendored Tableau Document Schemas\n\n"
        "XSD files synced from [tableau/tableau-document-schemas]"
        "(https://github.com/tableau/tableau-document-schemas).\n\n"
        f"Last synced: {__import__('datetime').datetime.now(tz=__import__('datetime').timezone.utc).isoformat()}\n"
    )
    readme_path.write_text(readme_content, encoding="utf-8")

    print(f"Synced {len(all_downloaded)} files to third_party/")


if __name__ == "__main__":
    main()
