"""Shared paths, scopes and credential loading for auth.py / server.py."""

from __future__ import annotations

import os
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"  # OAuth client (Desktop app) from Google Cloud Console
TOKENS_DIR = BASE_DIR / "tokens"  # one <account>.json per authorized mailbox
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]  # read/search/label/draft/send (no permanent delete)


def token_path(account: str) -> Path:
    return TOKENS_DIR / f"{account}.json"


def credentials_file(account: str) -> Path:
    """OAuth client to authorize `account` with: credentials-<account>.json if present, else the
    shared credentials.json.

    Accounts can live in different Google Cloud projects - e.g. a Workspace-internal app for a
    school address (no 7-day token expiry, but only that org's users) next to an external app for
    a personal address - and each project issues its own client.
    """
    per_account = BASE_DIR / f"credentials-{account}.json"
    return per_account if per_account.exists() else CREDENTIALS_FILE


def available_accounts() -> list[str]:
    if not TOKENS_DIR.exists():
        return []
    return sorted(p.stem for p in TOKENS_DIR.glob("*.json"))


def save_credentials(account: str, creds: Credentials) -> Path:
    TOKENS_DIR.mkdir(exist_ok=True)
    path = token_path(account)
    path.write_text(creds.to_json())
    os.chmod(path, 0o600)
    return path


def load_credentials(account: str) -> Credentials:
    path = token_path(account)
    if not path.exists():
        raise FileNotFoundError(f"No token for account '{account}'. Run: uv run auth.py {account}")
    creds = Credentials.from_authorized_user_file(str(path), SCOPES)
    if not creds.valid:
        if not (creds.expired and creds.refresh_token):
            raise RuntimeError(f"Token for '{account}' is unusable. Re-run: uv run auth.py {account}")
        try:
            creds.refresh(Request())
        except RefreshError as e:
            raise RuntimeError(
                f"Refresh failed for '{account}' ({e}). Re-run: uv run auth.py {account}. "
                "If this happens weekly, publish the OAuth consent screen to production."
            ) from e
        save_credentials(account, creds)
    return creds


def gmail_service(account: str):
    return build("gmail", "v1", credentials=load_credentials(account), cache_discovery=False)
