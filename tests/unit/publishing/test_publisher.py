"""Tests for TSC publisher and REST API fallback publisher.

All TSC and HTTP interactions are mocked -- no live server required.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import tableauserverclient as TSC

from tableau_agent_toolkit.publishing.fallback import RESTFallbackPublisher
from tableau_agent_toolkit.publishing.publisher import FILESIZE_LIMIT, TSCPublisher
from tableau_agent_toolkit.publishing.receipt import PublishReceipt
from tableau_agent_toolkit.security.settings import Settings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def settings():
    """Settings with dummy PAT credentials."""
    return Settings(
        server_url="https://tableau.example.com",
        pat_name="test-token",
        pat_secret="secret123",
        site_id="my-site",
    )


@pytest.fixture()
def twb_file(tmp_path):
    """Create a small temp .twb file for testing."""
    f = tmp_path / "test_workbook.twb"
    f.write_text("<workbook/>", encoding="utf-8")
    return f


@pytest.fixture()
def mock_project():
    """Mock project with id and name."""
    proj = MagicMock()
    proj.id = "test-project-uuid"
    proj.name = "Test Project"
    return proj


@pytest.fixture()
def mock_workbook_item():
    """Mock workbook item returned after publish."""
    wb = MagicMock()
    wb.id = "test-wb-uuid"
    wb.name = "test_workbook"
    return wb


def _make_mock_server(mock_project, mock_workbook_item):
    """Build a fully-mocked TSC Server for sync publish."""
    mock_server = MagicMock()

    # server.projects.filter returns iterable with mock_project
    mock_server.projects.filter.return_value = [mock_project]

    # server.workbooks.publish returns a workbook item (sync mode)
    mock_server.workbooks.publish.return_value = mock_workbook_item

    # server.auth.sign_in is a context manager
    mock_server.auth.sign_in.return_value.__enter__ = MagicMock(return_value=None)
    mock_server.auth.sign_in.return_value.__exit__ = MagicMock(return_value=False)

    return mock_server


# ---------------------------------------------------------------------------
# Test 1: publish creates receipt with expected fields
# ---------------------------------------------------------------------------


def test_publish_creates_receipt(settings, twb_file, mock_project, mock_workbook_item):
    mock_server = _make_mock_server(mock_project, mock_workbook_item)

    with patch("tableau_agent_toolkit.publishing.publisher.TSC") as mock_tsc:
        mock_tsc.Server.return_value = mock_server
        mock_tsc.PersonalAccessTokenAuth.return_value = MagicMock()
        mock_tsc.Server.PublishMode.CreateNew = TSC.Server.PublishMode.CreateNew
        mock_tsc.Server.PublishMode.Overwrite = TSC.Server.PublishMode.Overwrite
        mock_tsc.JobItem = TSC.JobItem
        mock_tsc.WorkbookItem = TSC.WorkbookItem

        publisher = TSCPublisher(settings)
        receipt = publisher.publish(twb_file, "Test Project")

    assert isinstance(receipt, PublishReceipt)
    assert receipt.workbook_id == "test-wb-uuid"
    assert receipt.project_name == "Test Project"
    assert receipt.mode == "CreateNew"
    assert receipt.server_url == "https://tableau.example.com"


# ---------------------------------------------------------------------------
# Test 2: publish resolves project by name
# ---------------------------------------------------------------------------


def test_publish_resolves_project_by_name(settings, twb_file, mock_project, mock_workbook_item):
    mock_server = _make_mock_server(mock_project, mock_workbook_item)

    with patch("tableau_agent_toolkit.publishing.publisher.TSC") as mock_tsc:
        mock_tsc.Server.return_value = mock_server
        mock_tsc.PersonalAccessTokenAuth.return_value = MagicMock()
        mock_tsc.Server.PublishMode.CreateNew = TSC.Server.PublishMode.CreateNew
        mock_tsc.Server.PublishMode.Overwrite = TSC.Server.PublishMode.Overwrite
        mock_tsc.JobItem = TSC.JobItem
        mock_tsc.WorkbookItem = TSC.WorkbookItem

        publisher = TSCPublisher(settings)
        publisher.publish(twb_file, "My Target Project")

    mock_server.projects.filter.assert_called_once_with(name="My Target Project")


# ---------------------------------------------------------------------------
# Test 3: publish with Overwrite mode
# ---------------------------------------------------------------------------


def test_publish_overwrite_mode(settings, twb_file, mock_project, mock_workbook_item):
    mock_server = _make_mock_server(mock_project, mock_workbook_item)

    with patch("tableau_agent_toolkit.publishing.publisher.TSC") as mock_tsc:
        mock_tsc.Server.return_value = mock_server
        mock_tsc.PersonalAccessTokenAuth.return_value = MagicMock()
        mock_tsc.Server.PublishMode.Overwrite = TSC.Server.PublishMode.Overwrite
        mock_tsc.Server.PublishMode.CreateNew = TSC.Server.PublishMode.CreateNew
        mock_tsc.JobItem = TSC.JobItem
        mock_tsc.WorkbookItem = TSC.WorkbookItem

        publisher = TSCPublisher(settings)
        publisher.publish(twb_file, "Test Project", mode="Overwrite")

    # Verify that publish was called with Overwrite mode
    call_args = mock_server.workbooks.publish.call_args
    assert call_args[0][2] == TSC.Server.PublishMode.Overwrite


# ---------------------------------------------------------------------------
# Test 4: publish with CreateNew mode
# ---------------------------------------------------------------------------


def test_publish_createnew_mode(settings, twb_file, mock_project, mock_workbook_item):
    mock_server = _make_mock_server(mock_project, mock_workbook_item)

    with patch("tableau_agent_toolkit.publishing.publisher.TSC") as mock_tsc:
        mock_tsc.Server.return_value = mock_server
        mock_tsc.PersonalAccessTokenAuth.return_value = MagicMock()
        mock_tsc.Server.PublishMode.CreateNew = TSC.Server.PublishMode.CreateNew
        mock_tsc.Server.PublishMode.Overwrite = TSC.Server.PublishMode.Overwrite
        mock_tsc.JobItem = TSC.JobItem
        mock_tsc.WorkbookItem = TSC.WorkbookItem

        publisher = TSCPublisher(settings)
        publisher.publish(twb_file, "Test Project", mode="CreateNew")

    call_args = mock_server.workbooks.publish.call_args
    assert call_args[0][2] == TSC.Server.PublishMode.CreateNew


# ---------------------------------------------------------------------------
# Test 5: async publish for large file (> 64MB)
# ---------------------------------------------------------------------------


def test_publish_async_for_large_file(settings, tmp_path, mock_project):
    # Create a real file
    large_file = tmp_path / "large_workbook.twbx"
    large_file.write_text("x", encoding="utf-8")

    # Mock workbook item returned after async job resolves
    mock_wb = MagicMock()
    mock_wb.id = "async-wb-uuid"
    mock_wb.name = "large_workbook"

    # Mock async job item
    mock_job = MagicMock(spec=TSC.JobItem)
    mock_job.workbook_id = "async-wb-uuid"
    mock_job.finish_code = 0

    mock_server = MagicMock()
    mock_server.projects.filter.return_value = [mock_project]
    mock_server.workbooks.publish.return_value = mock_job
    mock_server.jobs.wait_for_job.return_value = mock_job
    mock_server.workbooks.get_by_id.return_value = mock_wb
    mock_server.auth.sign_in.return_value.__enter__ = MagicMock(return_value=None)
    mock_server.auth.sign_in.return_value.__exit__ = MagicMock(return_value=False)

    with patch("tableau_agent_toolkit.publishing.publisher.TSC") as mock_tsc:
        mock_tsc.Server.return_value = mock_server
        mock_tsc.PersonalAccessTokenAuth.return_value = MagicMock()
        mock_tsc.Server.PublishMode.CreateNew = TSC.Server.PublishMode.CreateNew
        mock_tsc.Server.PublishMode.Overwrite = TSC.Server.PublishMode.Overwrite
        mock_tsc.JobItem = TSC.JobItem
        mock_tsc.WorkbookItem = TSC.WorkbookItem

        # Mock file size to be > 64MB
        with patch.object(Path, "stat") as mock_stat:
            mock_stat_result = MagicMock()
            mock_stat_result.st_size = 65 * 1024 * 1024  # 65MB
            mock_stat.return_value = mock_stat_result

            publisher = TSCPublisher(settings)
            receipt = publisher.publish(large_file, "Test Project")

    # Verify async mode was used
    call_kwargs = mock_server.workbooks.publish.call_args
    assert call_kwargs[1].get("as_job") is True or (
        len(call_kwargs[0]) > 3 and call_kwargs[0][3] is True
    )
    mock_server.jobs.wait_for_job.assert_called_once()
    assert receipt.workbook_id == "async-wb-uuid"


# ---------------------------------------------------------------------------
# Test 6: sync publish for small file (<= 64MB)
# ---------------------------------------------------------------------------


def test_publish_sync_for_small_file(settings, twb_file, mock_project, mock_workbook_item):
    mock_server = _make_mock_server(mock_project, mock_workbook_item)

    with patch("tableau_agent_toolkit.publishing.publisher.TSC") as mock_tsc:
        mock_tsc.Server.return_value = mock_server
        mock_tsc.PersonalAccessTokenAuth.return_value = MagicMock()
        mock_tsc.Server.PublishMode.CreateNew = TSC.Server.PublishMode.CreateNew
        mock_tsc.Server.PublishMode.Overwrite = TSC.Server.PublishMode.Overwrite
        mock_tsc.JobItem = TSC.JobItem
        mock_tsc.WorkbookItem = TSC.WorkbookItem

        publisher = TSCPublisher(settings)
        receipt = publisher.publish(twb_file, "Test Project")

    # Verify as_job was NOT set to True (sync publish)
    call_kwargs = mock_server.workbooks.publish.call_args
    # For small files, as_job should be False (keyword arg)
    assert call_kwargs[1].get("as_job") is False or (
        len(call_kwargs[0]) <= 3
    )
    # Jobs.wait_for_job should NOT be called
    mock_server.jobs.wait_for_job.assert_not_called()
    assert receipt.workbook_id == "test-wb-uuid"


# ---------------------------------------------------------------------------
# Test 7: project not found raises ValueError
# ---------------------------------------------------------------------------


def test_publish_project_not_found_raises_valueerror(settings, twb_file):
    mock_server = MagicMock()
    mock_server.projects.filter.return_value = []  # No projects returned
    mock_server.auth.sign_in.return_value.__enter__ = MagicMock(return_value=None)
    mock_server.auth.sign_in.return_value.__exit__ = MagicMock(return_value=False)

    with patch("tableau_agent_toolkit.publishing.publisher.TSC") as mock_tsc:
        mock_tsc.Server.return_value = mock_server
        mock_tsc.PersonalAccessTokenAuth.return_value = MagicMock()
        mock_tsc.Server.PublishMode.CreateNew = TSC.Server.PublishMode.CreateNew
        mock_tsc.Server.PublishMode.Overwrite = TSC.Server.PublishMode.Overwrite
        mock_tsc.JobItem = TSC.JobItem
        mock_tsc.WorkbookItem = TSC.WorkbookItem

        publisher = TSCPublisher(settings)
        with pytest.raises(ValueError, match="Project 'Missing Project' not found"):
            publisher.publish(twb_file, "Missing Project")


# ---------------------------------------------------------------------------
# Test 8: PAT secret not in string output
# ---------------------------------------------------------------------------


def test_pat_secret_not_in_str_output():
    settings = Settings(
        server_url="https://tableau.example.com",
        pat_name="test-token",
        pat_secret="secret123",
        site_id="my-site",
    )
    settings_str = str(settings)
    settings_repr = repr(settings)
    assert "secret123" not in settings_str
    assert "secret123" not in settings_repr


# ---------------------------------------------------------------------------
# Test 9: fallback publish uses requests with multipart/mixed
# ---------------------------------------------------------------------------


def test_fallback_publish_uses_requests(settings, twb_file):
    publisher = RESTFallbackPublisher(settings)

    # Mock sign-in response
    mock_sign_in_response = MagicMock()
    mock_sign_in_response.status_code = 200
    mock_sign_in_response.json.return_value = {
        "credentials": {"token": "test-auth-token", "site": {"id": "site-luid-123"}},
    }

    # Mock sites response for project resolution
    mock_sites_response = MagicMock()
    mock_sites_response.status_code = 200
    mock_sites_response.json.return_value = {
        "sites": {"site": [{"id": "site-luid-123", "contentUrl": "my-site"}]}
    }

    # Mock projects response
    mock_projects_response = MagicMock()
    mock_projects_response.status_code = 200
    mock_projects_response.json.return_value = {
        "projects": {
            "project": [{"id": "proj-uuid-123", "name": "Test Project"}]
        }
    }

    # Mock publish response
    mock_publish_response = MagicMock()
    mock_publish_response.status_code = 201
    mock_publish_response.json.return_value = {
        "workbook": {"id": "rest-wb-uuid", "name": "test_workbook"}
    }

    with patch("tableau_agent_toolkit.publishing.fallback.requests") as mock_requests:
        mock_requests.post.side_effect = [mock_sign_in_response, mock_publish_response]
        mock_requests.get.side_effect = [mock_sites_response, mock_projects_response]

        receipt = publisher.publish(twb_file, "Test Project")

    # Verify POST was called for sign-in and publish
    assert mock_requests.post.call_count == 2

    # Verify publish call used multipart/mixed content type
    publish_call = mock_requests.post.call_args_list[1]
    assert publish_call[1]["headers"]["Content-Type"] == "multipart/mixed"


# ---------------------------------------------------------------------------
# Test 10: fallback publish returns receipt
# ---------------------------------------------------------------------------


def test_fallback_publish_returns_receipt(settings, twb_file):
    publisher = RESTFallbackPublisher(settings)

    # Mock sign-in response
    mock_sign_in_response = MagicMock()
    mock_sign_in_response.status_code = 200
    mock_sign_in_response.json.return_value = {
        "credentials": {"token": "test-auth-token", "site": {"id": "site-luid-123"}},
    }

    # Mock sites response
    mock_sites_response = MagicMock()
    mock_sites_response.status_code = 200
    mock_sites_response.json.return_value = {
        "sites": {"site": [{"id": "site-luid-123", "contentUrl": "my-site"}]}
    }

    # Mock projects response
    mock_projects_response = MagicMock()
    mock_projects_response.status_code = 200
    mock_projects_response.json.return_value = {
        "projects": {
            "project": [{"id": "proj-uuid-123", "name": "Test Project"}]
        }
    }

    # Mock publish response
    mock_publish_response = MagicMock()
    mock_publish_response.status_code = 201
    mock_publish_response.json.return_value = {
        "workbook": {"id": "rest-wb-uuid", "name": "test_workbook"}
    }

    with patch("tableau_agent_toolkit.publishing.fallback.requests") as mock_requests:
        mock_requests.post.side_effect = [mock_sign_in_response, mock_publish_response]
        mock_requests.get.side_effect = [mock_sites_response, mock_projects_response]

        receipt = publisher.publish(twb_file, "Test Project")

    assert isinstance(receipt, PublishReceipt)
    assert receipt.workbook_id == "rest-wb-uuid"
    assert receipt.project_name == "Test Project"
    assert receipt.server_url == "https://tableau.example.com"


# ---------------------------------------------------------------------------
# Test 11: publish context manager signs in and out
# ---------------------------------------------------------------------------


def test_publish_context_manager_signs_out(settings, twb_file, mock_project, mock_workbook_item):
    mock_server = _make_mock_server(mock_project, mock_workbook_item)

    with patch("tableau_agent_toolkit.publishing.publisher.TSC") as mock_tsc:
        mock_tsc.Server.return_value = mock_server
        mock_tsc.PersonalAccessTokenAuth.return_value = MagicMock()
        mock_tsc.Server.PublishMode.CreateNew = TSC.Server.PublishMode.CreateNew
        mock_tsc.Server.PublishMode.Overwrite = TSC.Server.PublishMode.Overwrite
        mock_tsc.JobItem = TSC.JobItem
        mock_tsc.WorkbookItem = TSC.WorkbookItem

        publisher = TSCPublisher(settings)
        publisher.publish(twb_file, "Test Project")

    # Verify sign_in was used as a context manager
    mock_server.auth.sign_in.assert_called_once()
    # The context manager pattern means __enter__ and __exit__ were invoked
    mock_server.auth.sign_in.return_value.__enter__.assert_called_once()
    mock_server.auth.sign_in.return_value.__exit__.assert_called_once()
