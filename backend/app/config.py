from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    gemini_api_key: str
    gemini_model: str = "gemini-3.6-flash"
    github_token: str = ""

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    email_safe_mode: bool = True

    frontend_url: str = "http://localhost:3000"
    test_link: str = "https://forms.gle/mynachiketa-screening-test"

    # All scoring weights live here only.
    weight_resume: float = 0.30
    weight_ai_project: float = 0.20
    weight_github: float = 0.25
    weight_research: float = 0.10
    weight_cgpa: float = 0.15
    weight_test_logical: float = 0.40
    weight_test_coding: float = 0.60
    weight_pretest: float = 0.80
    weight_test: float = 0.20
    shortlist_threshold: float = 60.0
    interview_threshold: float = 70.0


settings = Settings()
