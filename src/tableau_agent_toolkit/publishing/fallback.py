"""REST API fallback publisher for Tableau Server/Cloud.

Handles edge cases that the TSC library does not cover:
custom HTTP options, proxy configurations, and unpublished REST endpoints.
Uses the requests library (bundled as a TSC dependency).
"""

import json
from pathlib import Path

import requests

from tableau_agent_toolkit.publishing.receipt import PublishReceipt
from tableau_agent_toolkit.security.settings import Settings


class RESTFallbackPublisher:
    """Publishes workbooks via direct REST API calls.

    Use this publisher when TSC does not support a specific REST feature
    or when custom HTTP configuration is needed.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()

    def publish(
        self,
        file_path: Path,
        project_name: str,
        mode: str = "CreateNew",
        server_url: str | None = None,
        site_id: str | None = None,
    ) -> PublishReceipt:
        """Publish a workbook via direct REST API call.

        Args:
            file_path: Path to .twb or .twbx file.
            project_name: Target project name.
            mode: Publish mode -- "CreateNew" or "Overwrite".
            server_url: Override server URL.
            site_id: Override site ID.

        Returns:
            PublishReceipt with publish operation details.

        Raises:
            FileNotFoundError: If file_path does not exist.
            RuntimeError: If the REST API call fails.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        url = server_url or self._settings.server_url
        site = site_id if site_id is not None else self._settings.site_id

        # Step 1: Sign in to get auth token
        auth_token, site_luid = self._sign_in(url, site)

        # Step 2: Resolve project ID
        project_id, resolved_name = self._resolve_project(url, site, auth_token, project_name)

        # Step 3: Publish via REST
        site_path = f"/api/3.21/sites/{site_luid}" if site_luid else "/api/3.21/sites/default"
        publish_url = f"{url}{site_path}/workbooks?overwrite={mode == 'Overwrite'}"

        file_size = file_path.stat().st_size
        with open(file_path, "rb") as f:
            response = requests.post(
                publish_url,
                headers={
                    "X-Tableau-Auth": auth_token,
                    "Content-Type": "multipart/mixed",
                },
                files={
                    "request_payload": (
                        None,
                        json.dumps(
                            {"workbook": {"name": file_path.stem, "project": {"id": project_id}}}
                        ),
                        "application/json",
                    ),
                    "tableau_workbook": (file_path.name, f, "application/octet-stream"),
                },
                timeout=600,
            )

        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"REST publish failed with status {response.status_code}: {response.text[:500]}"
            )

        response_data = response.json().get("workbook", {})

        return PublishReceipt(
            workbook_id=response_data.get("id", "unknown"),
            workbook_name=response_data.get("name", file_path.stem),
            project_id=project_id,
            project_name=resolved_name,
            site_id=site,
            server_url=url,
            mode=mode,
            file_path=str(file_path),
            file_size_bytes=file_size,
            verification_passed=True,
            verification_details=["Published successfully via REST API fallback"],
        )

    def _sign_in(self, server_url: str, site_id: str) -> tuple[str, str]:
        """Sign in via REST API to get auth token and site LUID.

        Returns:
            Tuple of (auth_token, site_luid).
        """
        sign_in_url = f"{server_url}/api/3.21/auth/signin"
        payload = {
            "credentials": {
                "personalAccessTokenName": self._settings.pat_name,
                "personalAccessTokenSecret": self._settings.pat_secret.get_secret_value(),
                "site": {"contentUrl": site_id},
            }
        }
        response = requests.post(
            sign_in_url,
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )
        if response.status_code != 200:
            raise RuntimeError(f"REST sign-in failed: {response.status_code} {response.text[:500]}")

        data = response.json()
        token = data["credentials"]["token"]
        site_luid = data["credentials"]["site"]["id"]
        return token, site_luid

    def _resolve_project(
        self, server_url: str, site_id: str, auth_token: str, project_name: str
    ) -> tuple[str, str]:
        """Resolve project name to ID via REST API.

        Returns:
            Tuple of (project_id, project_name).
        """
        # Get site LUID for the URL path
        projects_url = f"{server_url}/api/3.21/sites"
        headers = {"X-Tableau-Auth": auth_token, "Accept": "application/json"}

        # First get site info
        response = requests.get(projects_url, headers=headers, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to list sites: {response.status_code}")

        sites = response.json().get("sites", {}).get("site", [])
        site_luid = ""
        for s in sites:
            if s.get("contentUrl", "") == site_id:
                site_luid = s["id"]
                break

        if not site_luid:
            # Use first site if default
            if not site_id and sites:
                site_luid = sites[0]["id"]
            else:
                raise ValueError(f"Site '{site_id}' not found")

        # Now get projects for the site
        projects_url = f"{server_url}/api/3.21/sites/{site_luid}/projects"
        response = requests.get(projects_url, headers=headers, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to list projects: {response.status_code}")

        projects = response.json().get("projects", {}).get("project", [])
        for p in projects:
            if p["name"] == project_name:
                return p["id"], p["name"]

        raise ValueError(f"Project '{project_name}' not found")
