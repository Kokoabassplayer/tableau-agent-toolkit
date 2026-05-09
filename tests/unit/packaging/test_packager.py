"""Unit tests for WorkbookPackager and PackageVerifier.

Tests cover:
- Creating .twbx ZIP files from .twb files
- ZIP structure (root-level .twb, ZIP_DEFLATED compression)
- Asset inclusion in archives
- Output directory auto-creation
- .twbx verification (valid ZIP, parseable inner .twb)
- Error handling (corrupt ZIP, invalid XML, missing input)
"""

import zipfile
from pathlib import Path

import pytest
from lxml import etree

from tableau_agent_toolkit.packaging.packager import WorkbookPackager, PackageResult
from tableau_agent_toolkit.packaging.verifier import PackageVerifier, VerificationResult


class TestWorkbookPackager:
    """Tests for the WorkbookPackager.package() method."""

    @pytest.fixture()
    def sample_twb(self, tmp_path: Path) -> Path:
        """Create a minimal valid .twb fixture file."""
        twb_file = tmp_path / "test.twb"
        twb_file.write_text(
            '<workbook name="test"></workbook>', encoding="utf-8"
        )
        return twb_file

    def test_package_twb_creates_twbx(self, sample_twb: Path, tmp_path: Path) -> None:
        """Given a valid .twb file, WorkbookPackager.package() creates a .twbx ZIP file."""
        output = tmp_path / "output.twbx"
        packager = WorkbookPackager()
        result = packager.package(sample_twb, output)

        assert isinstance(result, PackageResult)
        assert result.output_path == output
        assert zipfile.is_zipfile(output)

    def test_package_twbx_contains_twb_at_root(
        self, sample_twb: Path, tmp_path: Path
    ) -> None:
        """The .twbx namelist() contains exactly the .twb filename with no directory prefix."""
        output = tmp_path / "output.twbx"
        packager = WorkbookPackager()
        packager.package(sample_twb, output)

        with zipfile.ZipFile(output, "r") as zf:
            names = zf.namelist()
            assert "test.twb" in names
            # Verify no directory prefix on the .twb entry
            for name in names:
                if name.endswith(".twb"):
                    assert name == "test.twb", (
                        f"Expected 'test.twb' but got '{name}'"
                    )

    def test_package_twbx_compression_is_deflated(
        self, sample_twb: Path, tmp_path: Path
    ) -> None:
        """The ZIP entry for the .twb uses ZIP_DEFLATED compression."""
        output = tmp_path / "output.twbx"
        packager = WorkbookPackager()
        packager.package(sample_twb, output)

        with zipfile.ZipFile(output, "r") as zf:
            info = zf.getinfo("test.twb")
            assert info.compress_type == zipfile.ZIP_DEFLATED

    def test_package_with_assets_includes_assets(
        self, sample_twb: Path, tmp_path: Path
    ) -> None:
        """When assets list is provided, the .twbx contains both the .twb and the assets."""
        # Create an asset file
        assets_dir = tmp_path / "Data"
        assets_dir.mkdir()
        asset_file = assets_dir / "extract.hyper"
        asset_file.write_bytes(b"\x00\x01\x02\x03")

        output = tmp_path / "output.twbx"
        packager = WorkbookPackager()
        result = packager.package(sample_twb, output, assets=[asset_file])

        with zipfile.ZipFile(output, "r") as zf:
            names = zf.namelist()
            assert "test.twb" in names
            assert "extract.hyper" in names

    def test_package_output_directory_created(
        self, sample_twb: Path, tmp_path: Path
    ) -> None:
        """If the output path's parent directory does not exist, it is created automatically."""
        nested_output = tmp_path / "nested" / "dir" / "output.twbx"
        packager = WorkbookPackager()
        result = packager.package(sample_twb, nested_output)

        assert nested_output.exists()
        assert zipfile.is_zipfile(nested_output)

    def test_package_nonexistent_input_raises_filenotfound(
        self, tmp_path: Path
    ) -> None:
        """Calling WorkbookPackager.package() with a nonexistent .twb path raises FileNotFoundError."""
        nonexistent = tmp_path / "does_not_exist.twb"
        output = tmp_path / "output.twbx"
        packager = WorkbookPackager()

        with pytest.raises(FileNotFoundError, match="TWB file not found"):
            packager.package(nonexistent, output)


class TestPackageVerifier:
    """Tests for the PackageVerifier.verify() method."""

    @pytest.fixture()
    def valid_twbx(self, tmp_path: Path) -> Path:
        """Create a valid .twbx using WorkbookPackager."""
        twb_file = tmp_path / "test.twb"
        twb_file.write_text(
            '<workbook name="test"></workbook>', encoding="utf-8"
        )
        output = tmp_path / "valid.twbx"
        packager = WorkbookPackager()
        packager.package(twb_file, output)
        return output

    def test_verify_valid_twbx_returns_valid(self, valid_twbx: Path) -> None:
        """Given a valid .twbx, verify() returns VerificationResult with valid=True."""
        verifier = PackageVerifier()
        result = verifier.verify(valid_twbx)

        assert isinstance(result, VerificationResult)
        assert result.valid is True
        assert result.errors == []

    def test_verify_corrupt_zip_returns_invalid(self, tmp_path: Path) -> None:
        """Given a file that is not a valid ZIP, verify() returns invalid with error message."""
        corrupt = tmp_path / "corrupt.twbx"
        corrupt.write_bytes(b"this is not a zip file at all")

        verifier = PackageVerifier()
        result = verifier.verify(corrupt)

        assert result.valid is False
        assert len(result.errors) > 0
        assert "Not a valid ZIP" in result.errors[0]

    def test_verify_twbx_with_invalid_inner_xml_returns_invalid(
        self, tmp_path: Path
    ) -> None:
        """Given a .twbx whose inner .twb has malformed XML, verify() returns invalid."""
        # Create a ZIP with a malformed .twb inside
        bad_twb = tmp_path / "bad.twb"
        bad_twb.write_text("<workbook><unclosed", encoding="utf-8")
        twbx_path = tmp_path / "bad.twbx"
        with zipfile.ZipFile(twbx_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(bad_twb, arcname="bad.twb")

        verifier = PackageVerifier()
        result = verifier.verify(twbx_path)

        assert result.valid is False
        assert len(result.errors) > 0
        # Error message should mention parse or XML
        error_text = " ".join(result.errors).lower()
        assert "parse" in error_text or "xml" in error_text
