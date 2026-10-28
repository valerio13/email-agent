"""Command line tools: connect Gmail once, and run the daily pipeline by hand.

uv run python -m app.cli authorize-gmail
uv run python -m app.cli run-pipeline
"""

import argparse
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.factory import get_llm_provider, get_mail_provider
from app.providers.mail.gmail import SCOPES, TOKEN_URI
from app.scheduler import run_pipeline


def authorize_gmail() -> None:
    """Open the Google consent page in the browser and print the refresh token it returns."""
    settings = get_settings()
    client_secret = settings.google_client_secret.get_secret_value()
    if not (settings.google_client_id and client_secret):
        sys.exit("Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env first.")

    client_config = {
        "installed": {
            "client_id": settings.google_client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": TOKEN_URI,
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    # offline + consent make Google return a refresh token every time, not only the first.
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    if not credentials.refresh_token:
        sys.exit("Google returned no refresh token. Revoke the app's access and try again.")
    print("\nAdd this line to your .env and restart the API. Keep it secret:\n")
    print(f"GOOGLE_REFRESH_TOKEN={credentials.refresh_token}")


def run_pipeline_once() -> None:
    """Fetch the new mail and analyse it now, instead of waiting for the daily run."""
    result = run_pipeline(get_session_factory(), get_mail_provider(), get_llm_provider())
    print(f"{result.new_emails} new emails, {result.analysed} analysed.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("authorize-gmail", help="connect Gmail and print the refresh token")
    commands.add_parser("run-pipeline", help="fetch and analyse the new mail now")
    args = parser.parse_args()
    if args.command == "authorize-gmail":
        authorize_gmail()
    else:
        run_pipeline_once()


if __name__ == "__main__":
    main()
