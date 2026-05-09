"""Semantic validation report types.

Defines the data structures for semantic validation results:
- Severity: issue severity levels (ERROR, WARNING, INFO)
- SemanticIssue: a single semantic validation finding
- SemanticValidationResult: aggregate result of a semantic validation run
"""

from dataclasses import dataclass, field
from enum import Enum

from lxml import etree


class Severity(str, Enum):
    """Severity level for a semantic validation issue."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class SemanticIssue:
    """A single semantic validation finding.

    Attributes:
        severity: How severe this issue is.
        category: Category of the issue (e.g., 'reference', 'naming').
        message: Human-readable description of the issue.
        xml_element: The XML element that caused the issue, if applicable.
        spec_ref: Reference to the spec section that is violated, if applicable.
        spec_file: Filename of the dashboard spec YAML, if applicable.
        spec_line: 1-based line number in the spec file, if applicable.
        remediation: Human-readable guidance for fixing the issue.
    """

    severity: Severity
    category: str
    message: str
    xml_element: etree._Element | None = None
    spec_ref: str | None = None
    spec_file: str | None = None
    spec_line: int | None = None
    remediation: str | None = None


@dataclass
class SemanticValidationResult:
    """Aggregate result of a semantic validation run.

    Attributes:
        valid: Whether the TWB file passed semantic validation (no errors).
        errors: List of issues with ERROR severity.
        warnings: List of issues with WARNING severity.
    """

    valid: bool
    errors: list[SemanticIssue] = field(default_factory=list)
    warnings: list[SemanticIssue] = field(default_factory=list)
