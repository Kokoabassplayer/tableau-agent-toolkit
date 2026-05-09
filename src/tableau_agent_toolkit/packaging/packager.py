"""Workbook packager that creates .twbx ZIP archives from .twb files.

Creates ZIP archives matching Tableau Desktop output structure:
the .twb at root level with ZIP_DEFLATED compression, plus optional
Data/ and Images/ assets.
"""

import zipfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PackageResult:
    """Result of a workbook packaging operation.

    Attributes:
        output_path: Path to the created .twbx file.
        warnings: Non-fatal warnings encountered during packaging.
    """

    output_path: Path
    warnings: list[str] = field(default_factory=list)


class WorkbookPackager:
    """Creates .twbx packaged workbooks from .twb files.

    Produces ZIP archives containing the .twb at root level with
    ZIP_DEFLATED compression, matching Tableau Desktop output format.
    Optionally includes additional assets (Data/, Images/ files).
    """

    def package(
        self,
        twb_path: Path,
        output_path: Path,
        assets: list[Path] | None = None,
    ) -> PackageResult:
        """Package a .twb file into a .twbx ZIP archive.

        Args:
            twb_path: Path to the source .twb file.
            output_path: Path for the output .twbx file.
            assets: Optional list of additional files to include
                (e.g., Data/extract.hyper, Images/logo.png).

        Returns:
            PackageResult with the output path and any warnings.

        Raises:
            FileNotFoundError: If twb_path does not exist.
        """
        if not twb_path.exists():
            raise FileNotFoundError(f"TWB file not found: {twb_path}")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Write the .twb as a root-level entry
            zf.write(twb_path, arcname=twb_path.name)

            # Include any additional assets at root level
            if assets:
                for asset in assets:
                    zf.write(asset, arcname=asset.name)

        return PackageResult(output_path=output_path)
