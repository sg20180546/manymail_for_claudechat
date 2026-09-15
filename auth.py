"""Authorize one Gmail account and store its token under tokens/<account>.json.

Usage:
    uv run auth.py gmail     # personal mailbox -> tokens/gmail.json
    uv run auth.py asu       # another mailbox  -> tokens/asu.json

The account name is just a local label; pick anything that is a valid identifier.
Opens a browser; pick the Google account you want to bind to that name.
"""

from __future__ import annotations

import sys

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from gmail_common import SCOPES, credentials_file, save_credentials


def main() -> int:
    args = sys.argv[1:]
    if len(args) != 1 or not args[0].isidentifier():
        print(__doc__)
        if len(args) > 1:
            print(f"ERROR: expected exactly one account name, got {args}\n"
                  "(zsh passes a trailing '# comment' as extra arguments - run it without the comment)")
        return 2
    account = args[0]
    creds_file = credentials_file(account)
    if not creds_file.exists():
        print(
            f"No OAuth client found for '{account}' (looked for credentials-{account}.json, "
            f"then credentials.json in {creds_file.parent})\n"
            "Google Cloud Console -> Google Auth Platform -> Clients -> "
            "Create client (Desktop app) -> Download JSON -> save it under one of those names"
        )
        return 1

    print(f"Using OAuth client: {creds_file.name}")
    flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
    # select_account: always show the account chooser (browser may be signed into several accounts)
    # consent: force a fresh grant so Google issues a refresh token
    creds = flow.run_local_server(port=0, prompt="select_account consent")

    path = save_credentials(account, creds)
    profile = build("gmail", "v1", credentials=creds, cache_discovery=False).users().getProfile(userId="me").execute()
    print(f"OK: account '{account}' -> {profile['emailAddress']}  (saved to {path})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
