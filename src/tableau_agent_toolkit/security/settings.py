"""Settings for Tableau Server credentials using pydantic-settings.

This is a stub for Phase 3 publisher credentials.
All fields are loaded from environment variables with the TABLEAU_ prefix.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Tableau Server connection settings loaded from environment variables.

    Set these via environment variables:
      TABLEAU_SERVER_URL    - Tableau Server URL (e.g. https://tableau.example.com)
      TABLEAU_PAT_NAME      - Personal Access Token name
      TABLEAU_PAT_SECRET    - Personal Access Token secret
      TABLEAU_SITE_ID       - Tableau site ID (empty string for default site)
    """

    model_config = SettingsConfigDict(env_prefix="TABLEAU_")

    # Placeholder fields for Phase 3 publisher credentials
    # tableau_server_url: str = ""
    # tableau_pat_name: str = ""
    # tableau_pat_secret: str = ""
    # tableau_site_id: str = ""
