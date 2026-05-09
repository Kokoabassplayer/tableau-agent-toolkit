"""TSC-based publisher for Tableau Server/Cloud workbooks.

Uses tableauserverclient (TSC) v0.40 as the primary publish backend.
Authenticates with PAT credentials, resolves project names to UUIDs,
and supports both sync and async (chunked) publish modes.
"""

from pathlib import Path

import tableauserverclient as TSC

from tableau_agent_toolkit.publishing.receipt import PublishReceipt
from tableau_agent_toolkit.security.settings import Settings


# TSC auto-chunks at this threshold (64MB)
FILESIZE_LIMIT = 64 * 1024 * 1024


class TSCPublisher:
    """Publishes workbooks to Tableau Server/Cloud via TSC.

    Uses PAT authentication and supports CreateNew/Overwrite modes.
    Files > 64MB automatically use async (chunked) upload.
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
        timeout: int = 600,
    ) -> PublishReceipt:
        """Publish a workbook file to Tableau Server/Cloud.

        Args:
            file_path: Path to .twb or .twbx file.
            project_name: Target project name (resolved to UUID).
            mode: Publish mode -- "CreateNew" or "Overwrite".
            server_url: Override server URL (uses settings if None).
            site_id: Override site ID (uses settings if None).
            timeout: Timeout in seconds for async job completion.

        Returns:
            PublishReceipt with publish operation details.

        Raises:
            FileNotFoundError: If file_path does not exist.
            ValueError: If project is not found on the server.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        url = server_url or self._settings.server_url
        site = site_id if site_id is not None else self._settings.site_id

        auth = TSC.PersonalAccessTokenAuth(
            token_name=self._settings.pat_name,
            personal_access_token=self._settings.pat_secret.get_secret_value(),
            site_id=site,
        )
        server = TSC.Server(url, use_server_version=True)

        with server.auth.sign_in(auth):
            # Resolve project name to UUID
            project_id = self._resolve_project(server, project_name)

            # Create workbook item
            wb_item = TSC.WorkbookItem(
                project_id=project_id,
                name=file_path.stem,
            )

            # Determine publish mode
            publish_mode = (
                TSC.Server.PublishMode.Overwrite
                if mode == "Overwrite"
                else TSC.Server.PublishMode.CreateNew
            )

            # Determine if async needed (file > 64MB)
            file_size = file_path.stat().st_size
            use_async = file_size > FILESIZE_LIMIT

            result = server.workbooks.publish(
                wb_item,
                str(file_path),
                publish_mode,
                as_job=use_async,
            )

            # Wait for async job if needed
            if isinstance(result, TSC.JobItem):
                job = server.jobs.wait_for_job(result, timeout=timeout)
                if job.finish_code != 0:
                    raise RuntimeError(
                        f"Async publish failed with finish_code={job.finish_code}"
                    )
                wb_item = server.workbooks.get_by_id(job.workbook_id)
            else:
                wb_item = result

        return PublishReceipt(
            workbook_id=wb_item.id,
            workbook_name=wb_item.name,
            project_id=project_id,
            project_name=project_name,
            site_id=site,
            server_url=url,
            mode=mode,
            file_path=str(file_path),
            file_size_bytes=file_size,
            verification_passed=True,
            verification_details=["Published successfully via TSC"],
        )

    def _resolve_project(self, server: TSC.Server, project_name: str) -> str:
        """Resolve a project name to its server-assigned UUID.

        Args:
            server: Authenticated TSC Server instance.
            project_name: Display name of the target project.

        Returns:
            Project UUID string.

        Raises:
            ValueError: If project not found.
        """
        for project in server.projects.filter(name=project_name):
            return project.id
        raise ValueError(f"Project '{project_name}' not found")
