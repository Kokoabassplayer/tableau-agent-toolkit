"""Pydantic v2 models for dashboard_spec.yaml schema.

These models define the typed contract for dashboard specifications.
Every other module in the toolkit consumes DashboardSpec objects.
"""

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class PackagingEnum(str, Enum):
    """Workbook packaging format."""

    twb = "twb"
    twbx = "twbx"


class TemplateSpec(BaseModel):
    """Reference to a TWB template file."""

    model_config = {"extra": "forbid"}

    id: str = Field(..., description="Logical template name")
    path: Path = Field(..., description="Path to source template workbook")
    required_anchors: list[str] = Field(
        default_factory=list,
        description="Anchor names that must exist in the template",
    )


class WorkbookSpec(BaseModel):
    """Workbook-level configuration."""

    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=1, description="Display name / filename base")
    target_tableau_version: str = Field(
        default="2026.1",
        description="Target Tableau version for generation",
    )
    packaging: PackagingEnum = Field(
        default=PackagingEnum.twb,
        description="Output format: twb (unpacked) or twbx (packaged)",
    )
    template: TemplateSpec = Field(..., description="Template reference for generation")


class DatasourceSpec(BaseModel):
    """Datasource definition within a workbook."""

    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=1, description="Datasource name")
    mode: str = Field(
        ...,
        description="Connection mode: published, embedded-live, embedded-extract, or custom-sql",
    )
    connection: dict | None = Field(
        default=None,
        description="Connection properties (server, database, etc.)",
    )
    custom_sql_file: str | None = Field(
        default=None,
        description="Path to custom SQL file (when mode=custom-sql)",
    )


class ParameterSpec(BaseModel):
    """Parameter definition within a workbook."""

    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=1, description="Parameter name")
    data_type: str = Field(..., description="Parameter data type (string, int, float, bool, date)")
    default_value: str | None = Field(default=None, description="Default parameter value")


class CalculationSpec(BaseModel):
    """Calculated field definition."""

    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=1, description="Calculation name")
    formula: str = Field(..., description="Tableau calculation formula")
    comment: str | None = Field(default=None, description="Optional comment for the calculation")


class WorksheetSpec(BaseModel):
    """Worksheet definition within a workbook."""

    model_config = {"extra": "forbid"}

    name: str = Field(..., min_length=1, description="Worksheet name")
    datasource: str | None = Field(
        default=None,
        description="Referenced datasource name",
    )


class PublishModeEnum(str, Enum):
    """Publish mode for workbook deployment."""

    CreateNew = "CreateNew"
    Overwrite = "Overwrite"


class PublishSpec(BaseModel):
    """Publish configuration within a dashboard spec."""

    model_config = {"extra": "forbid"}

    project: str = Field(..., min_length=1, description="Target project name on server")
    site_id: str = Field(default="", description="Target site contentUrl (empty for default)")
    mode: PublishModeEnum = Field(
        default=PublishModeEnum.CreateNew, description="Publish mode: CreateNew or Overwrite"
    )
    as_job: bool = Field(default=False, description="Use async publishing")
    skip_connection_check: bool = Field(
        default=False, description="Skip connection check at upload"
    )


class DashboardSpec(BaseModel):
    """Top-level dashboard specification model.

    This is the root model for dashboard_spec.yaml files. It validates
    the entire spec structure through Pydantic v2 and provides JSON Schema
    generation for editor support.
    """

    model_config = {"extra": "forbid"}

    spec_version: str = Field(
        default="1.0",
        description="Spec schema version",
    )
    workbook: WorkbookSpec = Field(..., description="Workbook configuration")
    datasources: list[DatasourceSpec] = Field(
        default_factory=list,
        description="Datasource definitions",
    )
    parameters: list[ParameterSpec] = Field(
        default_factory=list,
        description="Parameter definitions",
    )
    calculations: list[CalculationSpec] = Field(
        default_factory=list,
        description="Calculated field definitions",
    )
    worksheets: list[WorksheetSpec] = Field(
        default_factory=list,
        description="Worksheet definitions",
    )
    dashboards: list[dict] = Field(
        default_factory=list,
        description="Dashboard layout definitions",
    )
    publish: PublishSpec | None = Field(default=None, description="Publish configuration")
    qa: dict | None = Field(
        default=None,
        description="QA configuration (static checks, smoke tests)",
    )

    @classmethod
    def json_schema(cls) -> dict:
        """Generate JSON Schema for editor support (SPEC-05)."""
        return cls.model_json_schema()
