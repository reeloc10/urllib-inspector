# urllib-inspector

A lightweight, zero-dependency Python utility and importable module designed for inspecting URL headers, response codes, and bodies with strict UNIX stream hygiene.

## Features

- **Dual-Purpose Architecture:** Run it directly as a CLI tool (`urllib_inspector.py`) or import `inspect_url()` cleanly into your Python projects and bots.
- **Strict Stream Separation:** Status codes, warnings, and headers route exclusively to `stderr`, leaving `stdout` 100% pristine for data piping and file redirection.
- **No-Redirect Handling:** Built-in `NoRedirectHandler` prevents automatic 3xx redirection, letting you inspect intermediate redirect headers directly.
- **Silent Mode (-s):** Suppresses all metadata and headers for automated scripting and raw payload extraction.
- **ANSI Sanitization:** Automatically strips ANSI escape sequences and non-printable control characters to keep output clean and secure.

## Usage

### Command-Line Interface (CLI)

Inspect a URL interactively (metadata goes to stderr, body goes to stdout):
python3 urllib_inspector.py "https://example.com"

Save only the raw response body to a file cleanly, suppressing metadata:
python3 urllib_inspector.py -s "https://example.com" > output.html

### Python Module

from urllib_inspector import inspect_url

# Inspect a URL without following redirects
res = inspect_url("https://example.com", follow_redirects=False)

if res["success"]:
    print(f"Status Code: {res['status_code']}")
    print(f"Headers: {res['headers']}")
    print(f"Body: {res['body']}")
else:
    print(f"Error: {res['error']}")

## License

Licensed under the Apache License, Version 2.0. See the SPDX identifier header in urllib_inspector.py.
