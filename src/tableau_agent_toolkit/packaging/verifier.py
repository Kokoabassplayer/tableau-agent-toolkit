"""Package verifier that validates .twbx archive integrity.

Checks that a .twbx file is a valid ZIP archive containing a
parseable .twb XML file, using secure XML parser configuration.
"""

import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree


@dataclass
class VerificationResult:
    """Result of a .twbx verification operation.

    Attributes:
        valid: Whether the .twbx passed all verification checks.
        errors: List of error messages for any failed checks.
    """

    valid: bool
    errors: list[str] = field(default_factory=list)


class PackageVerifier:
    """Validates .twbx packaged workbook integrity.

    Checks that the file is a valid ZIP archive containing at least
    one .twb entry that parses as well-formed XML using a secure parser.
    """

    def verify(self, twbx_path: Path) -> VerificationResult:
        """Verify the integrity of a .twbx file.

        Args:
            twbx_path: Path to the .twbx file to verify.

        Returns:
            VerificationResult indicating validity and any errors found.
        """
        # Check that the file is a valid ZIP
        if not zipfile.is_zipfile(twbx_path):
            return VerificationResult(
                valid=False,
                errors=[f"Not a valid ZIP file: {twbx_path}"],
            )

        with zipfile.ZipFile(twbx_path, "r") as zf:
            # Find the .twb entry
            twb_entries = [name for name in zf.namelist() if name.endswith(".twb")]

            if not twb_entries:
                return VerificationResult(
                    valid=False,
                    errors=["No .twb file found in archive"],
                )

            # Read and parse the first .twb entry
            twb_content = zf.read(twb_entries[0])

            try:
                parser = etree.XMLParser(resolve_entities=False, no_network=True)
                etree.fromstring(twb_content, parser)
            except etree.XMLSyntaxError as exc:
                return VerificationResult(
                    valid=False,
                    errors=[f"Inner .twb failed to parse as XML: {exc}"],
                )

        return VerificationResult(valid=True)
