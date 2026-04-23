from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    project_root: Path
    data_dir: Path
    storage_dir: Path
    invoice_dir: Path
    temp_upload_dir: Path
    temp_session_dir: Path
    export_dir: Path
    database_url: str
    app_name: str = "MicroAccount"


def build_settings() -> Settings:
    project_root = Path(__file__).resolve().parent.parent
    data_dir = Path(os.getenv("LOGLUX_DATA_DIR", project_root / "data"))
    storage_dir = Path(os.getenv("LOGLUX_STORAGE_DIR", project_root / "storage"))
    invoice_dir = Path(os.getenv("LOGLUX_INVOICE_DIR", storage_dir / "invoices"))
    temp_upload_dir = Path(os.getenv("LOGLUX_TEMP_UPLOAD_DIR", storage_dir / "tmp_uploads"))
    temp_session_dir = Path(os.getenv("LOGLUX_TEMP_SESSION_DIR", data_dir / "temp_sessions"))
    export_dir = Path(os.getenv("LOGLUX_EXPORT_DIR", project_root / "exports"))
    database_url = os.getenv("LOGLUX_DATABASE_URL", f"sqlite:///{data_dir / 'accounting.db'}")
    app_name = os.getenv("LOGLUX_APP_NAME", "MicroAccount")
    return Settings(
        project_root=project_root,
        data_dir=data_dir,
        storage_dir=storage_dir,
        invoice_dir=invoice_dir,
        temp_upload_dir=temp_upload_dir,
        temp_session_dir=temp_session_dir,
        export_dir=export_dir,
        database_url=database_url,
        app_name=app_name,
    )


settings = build_settings()


def ensure_directories() -> None:
    for path in (
        settings.data_dir,
        settings.storage_dir,
        settings.invoice_dir,
        settings.temp_upload_dir,
        settings.temp_session_dir,
        settings.export_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)
