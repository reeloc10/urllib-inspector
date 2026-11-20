# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 reeloc10

import argparse
import json as json_lib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

# ANSI Color Constants
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
GRAY = "\033[90m"

# Comprehensive regex pattern to match ANSI escape sequences
ANSI_ESCAPE_PATTERN = re.compile(r'''
    \x1B  # ESC
    (?:   # 7-bit C1 Control (not CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
''', re.VERBOSE)

def sanitize_output(text: str) -> str:
    """Removes ANSI escape codes and non-printable control characters,
    while preserving standard whitespace (tabs, newlines) and UTF-8 characters.
    """
    if not isinstance(text, str):
        text = str(text)

    clean = ANSI_ESCAPE_PATTERN.sub('', text)
    clean = "".join(ch for ch in clean if ord(ch) >= 32 or ch in "\t\n\r")
    return clean

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def inspect_url(
    url,
    follow_redirects=False,
    stream_callback=None,
    data_items=None,
    raw_json=None,
    custom_headers=None,
    method=None
):
    """Core inspection function for library/bot usage.
    Supports GET, POST, PATCH, PUT with custom headers.
    Returns a dictionary with status, sanitized headers, sanitized body/payload, and effective URL.
    Accepts custom_headers as a dict ({"Key": "Value"}) or a list of strings (["Key: Value"]).
    """
    headers = {"User-Agent": "reeloc10-inspector/1.1"}

    if custom_headers:
        if isinstance(custom_headers, dict):
            for k, v in custom_headers.items():
                headers[str(k).strip()] = str(v).strip()
        else:
            for h in custom_headers:
                if ":" in str(h):
                    k, v = str(h).split(":", 1)
                    headers[k.strip()] = v.strip()

    # Determine HTTP method with fallback logic
    if method:
        req_method = method.upper()
    elif raw_json is not None or data_items:
        req_method = "POST"
    else:
        req_method = "GET"

    encoded_body = None

    if raw_json is not None:
        encoded_body = raw_json.encode("utf-8")
        headers.setdefault("Content-Type", "application/json")
    elif data_items:
        pairs = []
        for item in data_items:
            if "=" in item:
                k, v = item.split("=", 1)
                pairs.append((k, v))
        encoded_body = urllib.parse.urlencode(pairs).encode("utf-8")
        headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    req = urllib.request.Request(
        url,
        data=encoded_body,
        headers=headers,
        method=req_method
    )

    handlers = [NoRedirectHandler] if not follow_redirects else []
    opener = urllib.request.build_opener(*handlers)

    result = {
        "success": False,
        "status_code": None,
        "reason": None,
        "effective_url": sanitize_output(url),
        "headers": {},
        "body": None,
        "is_binary": False,
        "error": None
    }

    try:
        with opener.open(req) as response:
            result["success"] = True
            result["status_code"] = response.status
            result["reason"] = sanitize_output(response.reason) if response.reason else None
            result["effective_url"] = sanitize_output(response.url)
            result["headers"] = {
                sanitize_output(k): sanitize_output(v)
                for k, v in response.headers.items()
            }

            content_type = response.headers.get_content_type()
            main_type = response.headers.get_content_maintype()

            is_text = (
                main_type == "text" or
                content_type in {
                    "application/json", "application/javascript",
                    "application/xml", "application/xhtml+xml", "image/svg+xml"
                }
            )

            if is_text:
                raw_body = response.read().decode("utf-8", errors="replace")
                result["body"] = sanitize_output(raw_body)
                result["is_binary"] = False
            else:
                chunk_size = 8192
                downloaded = 0
                content_length = response.headers.get("Content-Length")
                total_size = int(content_length) if content_length and content_length.isdigit() else None

                chunks = []
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    downloaded += len(chunk)
                    if stream_callback:
                        stream_callback(downloaded, total_size)

                result["body"] = b"".join(chunks)
                result["is_binary"] = True

    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
        result["reason"] = sanitize_output(e.reason) if e.reason else None
        result["effective_url"] = sanitize_output(e.url)
        result["headers"] = {
            sanitize_output(k): sanitize_output(v)
            for k, v in e.headers.items()
        }
        result["body"] = e.read()

    except urllib.error.URLError as e:
        result["error"] = sanitize_output(str(e.reason))

    return result


def main():
    parser = argparse.ArgumentParser(description="Inspect URL headers and body with optional silence and POST support.")
    parser.add_argument("url", help="Target URL to inspect")
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress metadata and headers, print full body only")
    parser.add_argument("-d", "--data", action="append", help="Form field key=value (repeatable, triggers POST)")
    parser.add_argument("--json", dest="raw_json", help="Raw JSON payload string (triggers POST)")
    parser.add_argument("-H", "--header", action="append", help="Custom header 'Key: Value' (repeatable)")

    args = parser.parse_args()

    def progress_callback(downloaded, total_size):
        if not args.silent:
            if total_size:
                percent = (downloaded / total_size) * 100
                sys.stderr.write(f"\r{CYAN}[↓]{RESET} Downloading: {BOLD}{downloaded / (1024*1024):.2f} MB{RESET} / {total_size / (1024*1024):.2f} MB {YELLOW}({percent:.1f}%){RESET}")
            else:
                sys.stderr.write(f"\r{CYAN}[↓]{RESET} Downloaded: {BOLD}{downloaded / (1024*1024):.2f} MB{RESET}")
            sys.stderr.flush()

    try:
        res = inspect_url(
            args.url,
            follow_redirects=False,
            stream_callback=progress_callback,
            data_items=args.data,
            raw_json=args.raw_json,
            custom_headers=args.header
        )

        if res["error"]:
            print(f"{RED}[!] Network or URL Error: {res['error']}{RESET}", file=sys.stderr)
            sys.exit(1)

        status = res["status_code"]
        is_redirect_or_error = status >= 300

        if not args.silent:
            if res["is_binary"] and not is_redirect_or_error:
                sys.stderr.write("\n")  # Newline after progress bar

            if is_redirect_or_error:
                print(f"{YELLOW}[!] HTTP Status received (Redirect/Error):{RESET}", file=sys.stderr)
            else:
                print(f"{GREEN}[*] Request successful!{RESET}", file=sys.stderr)

            print(f"    {BOLD}Status Code:{RESET} {CYAN}{status}{RESET} {res['reason']}", file=sys.stderr)
            print(f"    {BOLD}Effective URL:{RESET} {res['effective_url']}", file=sys.stderr)

            print(f"\n{GRAY}--- Response Headers ---{RESET}", file=sys.stderr)
            for header, value in res["headers"].items():
                print(f"  {CYAN}{header}{RESET}: {value}", file=sys.stderr)
            print(file=sys.stderr)

        body = res["body"]

        if is_redirect_or_error:
            if args.silent:
                location = next((v for k, v in res["headers"].items() if k.lower() == "location"), None)
                if location:
                    print(sanitize_output(location))
                sys.exit(0 if 300 <= status < 400 else 1)

            if not body:
                print(f"{GRAY}No response body content{RESET}", file=sys.stderr)
            else:
                if isinstance(body, bytes):
                    decoded_body = body.decode("utf-8", errors="replace").strip()
                    if decoded_body:
                        print(f"{GRAY}--- Response Body ---{RESET}", file=sys.stderr)
                        print(sanitize_output(decoded_body), file=sys.stderr)
                elif str(body).strip():
                    print(f"{GRAY}--- Response Body ---{RESET}", file=sys.stderr)
                    print(sanitize_output(body), file=sys.stderr)

            sys.exit(0 if 300 <= status < 400 else 1)

        if not body or (isinstance(body, bytes) and len(body) == 0):
            if not args.silent:
                print(f"{GRAY}No response body content{RESET}", file=sys.stderr)
        else:
            if res["is_binary"]:
                if not args.silent:
                    content_type = res["headers"].get("content-type", "application/octet-stream")
                    print(f"{GRAY}--- Binary Payload ({content_type}, {len(body)} bytes) ---{RESET}", file=sys.stderr)
                sys.stdout.buffer.write(body)
                sys.stdout.flush()
            else:
                print(body)

    except KeyboardInterrupt:
        print(f"\n{RED}[!] Operation cancelled by user.{RESET}", file=sys.stderr)
        sys.exit(130)

if __name__ == "__main__":
    main()
