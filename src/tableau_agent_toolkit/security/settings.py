"""Settings for Tableau Server credentials using pydantic-settings.

Loads PAT credentials from environment variables with the TABLEAU_ prefix.
PAT secret is protected with SecretStr to prevent accidental logging.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Tableau Server connection settings loaded from environment variables.

    Set these via environment variables:
      TABLEAU_SERVER_URL    - Tableau Server URL (e.g. https://tableau.example.com)
      TABLEAU_PAT_NAME      - Personal Access Token name
      TABLEAU_PAT_SECRET    - Personal Access Token secret
      TABLEAU_SITE_ID       - Site contentUrl (empty string for default site)
    """

    model_config = SettingsConfigDict(env_prefix="TABLEAU_")

    server_url: str = ""
    pat_name: str = ""
    pat_secret: SecretStr = SecretStr("")
    site_id: str = ""
