"""Publish receipt model for recording publish operation outcomes."""

from datetime import datetime

from pydantic import BaseModel, Field


class PublishReceipt(BaseModel):
    """Receipt confirming a workbook publish operation.

    Records the outcome of publishing a workbook to Tableau Server/Cloud,
    including the server-assigned workbook ID, target project/site, and
    verification status.
    """

    model_config = {"extra": "forbid"}

    workbook_id: str = Field(..., description="Server-assigned workbook UUID")
    workbook_name: str = Field(..., description="Published workbook name")
    project_id: str = Field(..., description="Target project UUID")
    project_name: str = Field(..., description="Target project name")
    site_id: str = Field(..., description="Target site contentUrl")
    server_url: str = Field(..., description="Tableau Server URL")
    mode: str = Field(..., description="Publish mode: CreateNew or Overwrite")
    published_at: datetime = Field(default_factory=datetime.now, description="Timestamp of publish")
    file_path: str = Field(..., description="Path of published file")
    file_size_bytes: int = Field(..., description="Published file size in bytes")
    verification_passed: bool = Field(
        default=True, description="Post-publish verification result"
    )
    verification_details: list[str] = Field(
        default_factory=list, description="Verification check details"
    )
