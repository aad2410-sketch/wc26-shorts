"""One-time local helper: run the installed-app OAuth flow and print the
refresh token to store as the YT_REFRESH_TOKEN GitHub secret.

Usage:
    python scripts/get_youtube_token.py CLIENT_ID CLIENT_SECRET
"""
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    client_id, client_secret = sys.argv[1], sys.argv[2]
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        },
        SCOPES,
    )
    creds = flow.run_local_server(port=0, prompt="consent")
    print("\n=== SUCCESS - add these GitHub secrets ===")
    print(f"YT_CLIENT_ID:     {client_id}")
    print(f"YT_CLIENT_SECRET: {client_secret}")
    print(f"YT_REFRESH_TOKEN: {creds.refresh_token}")


if __name__ == "__main__":
    main()
