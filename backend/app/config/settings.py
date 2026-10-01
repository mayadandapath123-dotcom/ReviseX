"""Application configuration.

Everything is env-driven so the same code runs on a student laptop, a dev box
and (later) a hosted instance. No secrets are ever exposed to the frontend.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="ReviseX", alias="APP_NAME")
    environment: str = Field(default="development", alias="APP_ENV")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    # Local-first data
    data_dir: Path = Field(default=BACKEND_ROOT / "data", alias="DATA_DIR")
    db_filename: str = Field(default="revise.sqlite3", alias="DB_FILENAME")
    content_dir: Path = Field(default=BACKEND_ROOT / "content", alias="CONTENT_DIR")

    # Content policy
    allow_off_syllabus: bool = Field(default=False, alias="ALLOW_OFF_SYLLABUS")
    auto_approve_ai_items: bool = Field(
        default=False,
        alias="AUTO_APPROVE_AI_ITEMS",
        description="Never enable in production: AI items go to a review queue by default.",
    )

    # AI provider selection (all optional)
    ai_provider: str = Field(default="local", alias="AI_PROVIDER")  # local|ollama|free_api|paid_api|none
    ollama_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_URL")
    ollama_model: str = Field(default="llama3.2:3b", alias="OLLAMA_MODEL")
    ollama_timeout_s: float = Field(default=20.0, alias="OLLAMA_TIMEOUT_S")
    free_api_url: str | None = Field(default=None, alias="FREE_AI_API_URL")
    # Keys stay server-side only; they are never serialised into any response.
    free_api_key: str | None = Field(default=None, alias="FREE_AI_API_KEY")
    paid_api_key: str | None = Field(default=None, alias="PAID_AI_API_KEY")

    # When set to a postgresql:// URL (e.g. Neon), the app runs on Postgres and
    # the local SQLite file is ignored. Unset means local-first SQLite.
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    # ── Google sign-in (all optional; the feature hides itself when unset) ──
    # Create these in Google Cloud Console -> APIs & Services -> Credentials ->
    # OAuth client ID (Web application). The secret is server-side only and is
    # never sent to the browser.
    google_client_id: str | None = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    # Must match EXACTLY one of the Authorized redirect URIs in Google Cloud
    # Console, including scheme and trailing slash behaviour.
    google_redirect_uri: str | None = Field(default=None, alias="GOOGLE_REDIRECT_URI")
    # Public origin of the deployed app, used to derive the redirect URI when
    # it is not given explicitly. No trailing slash.
    public_base_url: str | None = Field(default=None, alias="PUBLIC_BASE_URL")

    # ── Admin ──
    # Comma-separated usernames granted admin on boot. Bootstrapping from an
    # environment variable means the first admin does not have to be promoted
    # by an existing admin, which is otherwise a chicken-and-egg problem.
    admin_usernames: str = Field(default="", alias="ADMIN_USERNAMES")

    # ── Account-free ("local") profiles ──
    # On a single-user install these are the whole point: pick a name, play,
    # nothing to remember. On a PUBLIC server they are a liability - every
    # anonymous visitor writes a row into one shared database, the rows have no
    # owner, and anyone who learns an id can claim that progress at signup.
    # Turn the path off in production; existing local profiles can still be
    # claimed, this only stops new ones being created.
    allow_local_profiles: bool = Field(default=True, alias="ALLOW_LOCAL_PROFILES")
    max_local_profiles: int = Field(default=12, alias="MAX_LOCAL_PROFILES")

    client_version: str = Field(default="0.1.0", alias="CLIENT_VERSION")

    @property
    def google_enabled(self) -> bool:
        """Google sign-in is usable only with both an id and a secret."""
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def resolved_redirect_uri(self) -> str:
        if self.google_redirect_uri:
            return self.google_redirect_uri
        base = (self.public_base_url or "").rstrip("/")
        return f"{base}{self.api_prefix}/auth/google/callback"

    @property
    def admin_username_set(self) -> set[str]:
        return {u.strip().lower() for u in self.admin_usernames.split(",") if u.strip()}

    @property
    def db_path(self) -> Path:
        return self.data_dir / self.db_filename

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
