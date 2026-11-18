# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 reeloc10

import os
import sys

# Dynamically add the target folder to Python's import search path
# Example: pointing to a folder named 'common_tools' one level up or absolute path
target_file_abs = os.path.realpath(sys.argv[0])
target_dir = os.path.dirname(target_file_abs)

dependency_dir = os.path.abspath(f"{target_dir}/..")
if dependency_dir not in sys.path:
    sys.path.insert(0, dependency_dir)

import urllib_inspector

TOKEN_URL = "https://id.twitch.tv/oauth2/token"
DEVICE_URL = "https://id.twitch.tv/oauth2/device"
VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"


def test_twitch_device_init(client_id: str) -> None:
    """Initiate Device Code authorization flow via POST form-data."""
    print(f"[*] Requesting Device Code from Twitch for Client ID: {client_id}")

    res = urllib_inspector.inspect_url(
        DEVICE_URL,
        follow_redirects=False,
        data_items=[
            f"client_id={client_id}",
            "scopes=user:read:chat user:write:chat user:bot"
        ]
    )

    if res["success"] and res["status_code"] == 200:
        print("[+] Device Auth Response:")
        print(res["body"])
    else:
        print(f"[!] Error {res['status_code']}: {res['body']}", file=sys.stderr)


def test_twitch_token_exchange(client_id: str, client_secret: str) -> None:
    """Request an App Access Token via POST form-data."""
    print("[*] Requesting App Access Token from Twitch...")

    res = urllib_inspector.inspect_url(
        TOKEN_URL,
        follow_redirects=False,
        data_items=[
            f"client_id={client_id}",
            f"client_secret={client_secret}",
            "grant_type=client_credentials"
        ]
    )

    if res["success"] and res["status_code"] == 200:
        print("[+] Token Exchange Success:")
        print(res["body"])
    else:
        print(f"[!] Error {res['status_code']}: {res['body']}", file=sys.stderr)


def test_twitch_token_validation(access_token: str) -> None:
    """Verify an existing token via GET with custom Authorization header."""
    print("[*] Validating token against Twitch...")

    res = urllib_inspector.inspect_url(
        VALIDATE_URL,
        follow_redirects=False,
        custom_headers=[f"Authorization: OAuth {access_token}"]
    )

    if res["success"] and res["status_code"] == 200:
        print("[+] Token is valid:")
        print(res["body"])
    else:
        print(f"[!] Validation failed ({res['status_code']}): {res['body']}", file=sys.stderr)


if __name__ == "__main__":
    # Example structure using placeholder strings until secret handling is configured
    dummy_id = "placeholder_client_id"
    dummy_secret = "placeholder_client_secret"
    dummy_token = "placeholder_access_token"

    # Uncomment whichever endpoint you want to test
    test_twitch_device_init(dummy_id)
    test_twitch_token_exchange(dummy_id, dummy_secret)
    test_twitch_token_validation(dummy_token)
