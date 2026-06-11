"""One-time local helper for Instagram Graph API credentials.

Step 1 (browser): Graph API Explorer -> select your app -> add permissions
  instagram_basic, instagram_content_publish, pages_show_list,
  pages_read_engagement, business_management
  -> Generate Access Token (this is SHORT-lived).

Step 2: exchange it for a LONG-lived token (60 days) and find your IG user id:
    python scripts/get_ig_token.py APP_ID APP_SECRET SHORT_LIVED_TOKEN

Refresh before expiry (re-run step 2 with the long-lived token).
"""
import sys

import requests

GRAPH = "https://graph.facebook.com/v23.0"


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    app_id, app_secret, short_token = sys.argv[1:4]

    resp = requests.get(
        f"{GRAPH}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    long_token = resp.json()["access_token"]

    pages = requests.get(
        f"{GRAPH}/me/accounts",
        params={"access_token": long_token},
        timeout=30,
    ).json().get("data", [])

    ig_id = None
    for page in pages:
        detail = requests.get(
            f"{GRAPH}/{page['id']}",
            params={"fields": "instagram_business_account",
                    "access_token": long_token},
            timeout=30,
        ).json()
        if "instagram_business_account" in detail:
            ig_id = detail["instagram_business_account"]["id"]
            print(f"Found IG business account on page '{page.get('name')}'")
            break

    print("\n=== SUCCESS - add these GitHub secrets ===")
    print(f"IG_ACCESS_TOKEN: {long_token}")
    print(f"IG_USER_ID:      {ig_id or 'NOT FOUND - link IG to a FB Page first'}")
    print("\nToken lasts ~60 days. Re-run this script (pass the long-lived token")
    print("as SHORT_LIVED_TOKEN) before it expires to refresh.")


if __name__ == "__main__":
    main()
