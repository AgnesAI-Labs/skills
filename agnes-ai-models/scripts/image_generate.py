#!/usr/bin/env python3
"""Generate or edit an image with Agnes AI and print the result.

Purpose
    Call the Agnes images endpoint (model agnes-image-2.1-flash) for
    text-to-image generation, or image-to-image editing when --image is
    given. By default the script prints a JSON summary (including the
    image URL when the API returns one) and writes nothing to disk.
    Files are saved only when --output is explicitly provided.

Dependencies
    pip install openai   (httpx, used for downloading result images,
                          is installed with openai)

Environment
    AGNES_API_KEY   Required. An exported environment variable is used
                    first; that covers shell startup files (~/.bashrc,
                    ~/.zshrc) on macOS/Linux and user or system
                    environment variables on Windows. If unset, .env
                    files are checked in order: ./.env.local, ./.env,
                    <skill dir>/.env.local, <skill dir>/.env,
                    ~/.env.local, ~/.env (an AGNES_API_KEY=... line,
                    optional quotes, optional export prefix). Never
                    hardcode the key or commit a .env file.
    AGNES_BASE_URL  Optional. Defaults to https://apihub.agnes-ai.com/v1.
                    If the primary international route fails at the
                    network level (DNS, TLS, connection timeout), the
                    script retries once with https://apihub.agnes-ai.cn/v1.
                    HTTP status errors (400/401/403/422/429, ...) never
                    trigger a route change; keep the selected route and
                    check the request instead. See
                    references/troubleshooting.md.

Minimal example
    export AGNES_API_KEY="your_api_key_here"
    python scripts/image_generate.py \
        --prompt "A clean product photo of a matte black headphone" \
        --size 1024x768

    # Save to disk only when you ask for it:
    python scripts/image_generate.py --prompt "..." --output ./out/

Error handling
    Exit codes: 0 success, 1 API or runtime failure, 2 missing
    AGNES_API_KEY or bad command-line usage. Transient HTTP errors
    (408, 429, 500, 502, 503, 504, 520, 522, 524) are retried with
    exponential backoff before failing. Diagnostics go to stderr;
    the JSON result goes to stdout. The API key is never printed.

Notes
    The API may return either a URL or base64 data for an image; this
    script accepts both. Agnes has been observed to return a URL even
    when base64 output is requested, so the result is handled
    defensively.

Source & License
    Original work contributed to AgnesAI-Labs/skills under the MIT
    License (https://opensource.org/licenses/MIT). The author
    irrevocably grants this repository full rights to use, modify,
    sublicense, and redistribute this code with no further attribution
    or permission required.
"""

import argparse
import base64
import json
import os
import sys

import httpx
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
)

PRIMARY_URL = "https://apihub.agnes-ai.com/v1"
FALLBACK_URL = "https://apihub.agnes-ai.cn/v1"
DEFAULT_MODEL = "agnes-image-2.1-flash"
DEFAULT_SIZE = "1024x768"

IMAGE_MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def env_file_candidates():
    """Well-known .env locations, checked in priority order."""
    skill_dir = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
    home_dir = os.path.expanduser("~")
    cwd = os.getcwd()
    return [
        os.path.join(cwd, ".env.local"),
        os.path.join(cwd, ".env"),
        os.path.join(skill_dir, ".env.local"),
        os.path.join(skill_dir, ".env"),
        os.path.join(home_dir, ".env.local"),
        os.path.join(home_dir, ".env"),
    ]


def resolve_api_key():
    """Resolve AGNES_API_KEY from the environment or .env files.

    Returns (key, source_path); source_path is None when the key came
    from the environment. An exported environment variable wins, which
    covers shell startup files (~/.bashrc, ~/.zshrc) on macOS/Linux
    and user or system environment variables on Windows. Otherwise
    .env / .env.local files in the current directory, skill directory,
    and home directory are checked in that order. A line like
    AGNES_API_KEY=value is read; surrounding quotes and a leading
    export keyword are tolerated.
    """
    key = os.environ.get("AGNES_API_KEY")
    if key:
        return key, None
    for path in env_file_candidates():
        try:
            with open(path, encoding="utf-8") as handle:
                for raw in handle:
                    line = raw.strip()
                    if line.startswith("export "):
                        line = line[7:].strip()
                    if not line.startswith("AGNES_API_KEY="):
                        continue
                    value = line.split("=", 1)[1].strip()
                    if (
                        value[:1] in "\"'"
                        and value[:1] == value[-1:]
                    ):
                        value = value[1:-1]
                    if value:
                        return value, path
        except OSError:
            continue
    return None, None


def image_to_data_url(path):
    """Encode a local image file as a data URL for the API payload."""
    suffix = os.path.splitext(path)[1].lower()
    mime = IMAGE_MIME_BY_SUFFIX.get(suffix, "image/png")
    with open(path, "rb") as handle:
        encoded = base64.b64encode(handle.read()).decode("ascii")
    return "data:{0};base64,{1}".format(mime, encoded)


def as_image_ref(value):
    """Return value as an image URL, encoding local files as data URLs."""
    if value.startswith(("http://", "https://", "data:")):
        return value
    if not os.path.isfile(value):
        raise FileNotFoundError("Image file not found: {0}".format(value))
    return image_to_data_url(value)


def run_with_route_fallback(base_url, api_key, call):
    """Run call(client); retry once on the alternate international route.

    Only network-level failures (DNS, TLS, connection timeout) may
    trigger a route change, and only when the failing route is the
    international primary. HTTP status errors (400/401/403/422/429, ...)
    are raised as-is: keep the selected route and check the request,
    key, account, permissions, or rate limits instead.
    """
    # max_retries: exponential backoff for transient HTTP errors
    # (408/429/500/502/503/504/520/522/524), per SKILL.md guidance.
    client = OpenAI(api_key=api_key, base_url=base_url, max_retries=3)
    try:
        return call(client)
    except (APIConnectionError, APITimeoutError):
        if base_url != PRIMARY_URL:
            raise
        print(
            "Primary route unreachable; retrying with {0}".format(
                FALLBACK_URL
            ),
            file=sys.stderr,
        )
        client = OpenAI(
            api_key=api_key, base_url=FALLBACK_URL, max_retries=3
        )
        return call(client)


def summarize_item(index, item):
    """Build a stdout-safe summary of one generated image."""
    b64_json = getattr(item, "b64_json", None)
    summary = {
        "index": index,
        "url": getattr(item, "url", None),
        "has_base64": bool(b64_json),
        "revised_prompt": getattr(item, "revised_prompt", None),
    }
    if b64_json and not summary["url"]:
        summary["base64_length"] = len(b64_json)
    return summary


def download_url(url, path, timeout=120.0):
    """Download url to path (with timeout, following redirects)."""
    with httpx.stream(
        "GET", url, timeout=timeout, follow_redirects=True
    ) as response:
        response.raise_for_status()
        with open(path, "wb") as handle:
            for chunk in response.iter_bytes():
                handle.write(chunk)


def save_item(item, destination, index, total):
    """Save one generated image; return the written file path."""
    if os.path.isdir(destination) or destination.endswith(os.sep):
        os.makedirs(destination, exist_ok=True)
        path = os.path.join(
            destination, "agnes_image_{0:03d}.png".format(index)
        )
    else:
        if total > 1:
            raise ValueError(
                "--output must be a directory when --n > 1"
            )
        parent = os.path.dirname(os.path.abspath(destination))
        os.makedirs(parent, exist_ok=True)
        path = destination

    b64_json = getattr(item, "b64_json", None)
    url = getattr(item, "url", None)
    if b64_json:
        with open(path, "wb") as handle:
            handle.write(base64.b64decode(b64_json))
    elif url:
        download_url(url, path)
    else:
        raise ValueError(
            "Image {0} has neither base64 data nor a URL".format(index)
        )
    return path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate or edit an image with Agnes AI."
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Image generation prompt.",
    )
    parser.add_argument(
        "--size",
        default=DEFAULT_SIZE,
        help="Output size, e.g. 1024x768, 1024x1024 (default: 1024x768).",
    )
    parser.add_argument(
        "--image",
        default=None,
        help="Reference image path or URL for image-to-image editing.",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=1,
        help="Number of images to generate (default: 1).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model name (default: agnes-image-2.1-flash).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Save images to this path (directory or file). "
            "Nothing is written to disk unless this is set."
        ),
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()

    api_key, key_source = resolve_api_key()
    if not api_key:
        lines = [
            "AGNES_API_KEY not found.",
            "Export it (e.g. ~/.bashrc or ~/.zshrc on macOS/Linux,",
            "user environment variables on Windows), or add",
            "AGNES_API_KEY=... to one of:",
        ]
        lines.extend("  " + path for path in env_file_candidates())
        print("\n".join(lines), file=sys.stderr)
        return 2
    if key_source:
        print(
            "Using AGNES_API_KEY from {0}".format(key_source),
            file=sys.stderr,
        )

    base_url = os.environ.get("AGNES_BASE_URL", PRIMARY_URL).rstrip("/")
    print("Using AGNES_BASE_URL={0}".format(base_url), file=sys.stderr)

    image_ref = None
    if args.image:
        try:
            image_ref = as_image_ref(args.image)
        except OSError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    def call(client):
        extra_body = {}
        if image_ref:
            extra_body["image"] = [image_ref]
        return client.images.generate(
            model=args.model,
            prompt=args.prompt,
            size=args.size,
            n=args.n,
            extra_body=extra_body or None,
        )

    try:
        response = run_with_route_fallback(base_url, api_key, call)
    except APIStatusError as exc:
        print(
            "API error: {0} {1}".format(exc.status_code, exc.message),
            file=sys.stderr,
        )
        return 1
    except (APIConnectionError, APITimeoutError) as exc:
        print("Connection failed: {0}".format(exc), file=sys.stderr)
        return 1

    items = list(response.data)
    if not items:
        print("No images returned.", file=sys.stderr)
        return 1

    saved_files = []
    if args.output:
        try:
            for index, item in enumerate(items):
                path = save_item(
                    item, args.output, index, len(items)
                )
                saved_files.append(path)
                print("Saved {0}".format(path), file=sys.stderr)
        except (OSError, ValueError, httpx.HTTPError) as exc:
            print("Save failed: {0}".format(exc), file=sys.stderr)
            return 1

    result = {
        "created": getattr(response, "created", None),
        "images": [
            summarize_item(index, item)
            for index, item in enumerate(items)
        ],
        "saved_files": saved_files,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
