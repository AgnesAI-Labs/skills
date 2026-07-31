#!/usr/bin/env python3
"""Analyze an image with Agnes AI and print the model response.

Purpose
    Send one image (local file or public URL) plus an instruction to the
    Agnes chat completions endpoint (model agnes-2.5-flash) and print the
    analysis. Supports plain text, structured markdown, and JSON output.

Dependencies
    pip install openai

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
    AGNES_MODEL     Optional. Overrides the default vision model.

Minimal example
    export AGNES_API_KEY="your_api_key_here"
    python scripts/image_understand.py \
        --image photo.jpg \
        --prompt "Describe what is in this image."

Error handling
    Exit codes: 0 success, 1 API or runtime failure, 2 missing
    AGNES_API_KEY or bad command-line usage. Diagnostics go to stderr;
    only the model reply goes to stdout. The API key is never printed.
    Transient HTTP errors (408, 429, 500, 502, 503, 504, 520, 522,
    524) are retried with exponential backoff before failing.

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
import re
import shutil
import subprocess
import sys

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
)

PRIMARY_URL = "https://apihub.agnes-ai.com/v1"
FALLBACK_URL = "https://apihub.agnes-ai.cn/v1"
DEFAULT_MODEL = "agnes-2.5-flash"
DEFAULT_MAX_TOKENS = 2048

IMAGE_MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}

STRUCTURED_SUFFIX = (
    "\n\nProvide a structured analysis with the following sections:\n"
    "- Summary (one sentence)\n"
    "- Description (detailed)\n"
    "- Subjects\n"
    "- Style\n"
    "- Color palette\n"
    "- Composition\n"
    "- Mood\n"
    "- Text in image (if any)\n"
    "- Metadata (dimensions, aspect ratio, format)"
)

JSON_SUFFIX = (
    "\n\nReturn the result as valid JSON matching this schema:\n"
    "{\n"
    '  "summary": "string",\n'
    '  "description": "string",\n'
    '  "subjects": ["string"],\n'
    '  "style": "string",\n'
    '  "color_palette": ["string"],\n'
    '  "composition": "string",\n'
    '  "mood": "string",\n'
    '  "text_in_image": "string",\n'
    '  "metadata": {"width": 0, "height": 0, '
    '"aspect_ratio": "string", "format": "string"}\n'
    "}"
)


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


def describe_local_image(path):
    """Best-effort dimensions via ffprobe; empty if unavailable."""
    if shutil.which("ffprobe") is None:
        return ""
    try:
        completed = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    dimensions = completed.stdout.strip()
    if "x" not in dimensions:
        return ""
    width, height = dimensions.split("x", 1)
    return (
        "Image metadata: width={0}, height={1}, "
        "aspect_ratio={0}:{1}.".format(width, height)
    )


def build_prompt(user_prompt, output_format, metadata):
    """Compose the full instruction for the requested output format."""
    if output_format == "text":
        return user_prompt
    if output_format == "json":
        suffix = JSON_SUFFIX
    else:
        suffix = STRUCTURED_SUFFIX
    if metadata:
        return user_prompt + suffix + "\n\n" + metadata
    return user_prompt + suffix


def strip_code_fences(text):
    """Remove optional ```json fences models sometimes add."""
    match = re.search(r"```(?:json)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    return match.group(1) if match else text


def create_chat_completion(client, args, prompt_text, image_ref):
    """Call chat completions with one text part and one image part."""
    return client.chat.completions.create(
        model=args.model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_ref},
                    },
                ],
            }
        ],
        max_tokens=args.max_tokens,
    )


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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Analyze an image with Agnes AI chat completions."
    )
    parser.add_argument(
        "--image",
        required=True,
        help="Local image path or publicly accessible URL.",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Analysis instruction for the model.",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "structured", "json"),
        default="structured",
        help="Output format (default: structured).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Alias for --format json.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("AGNES_MODEL", DEFAULT_MODEL),
        help="Vision model (default: agnes-2.5-flash or AGNES_MODEL).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help="Maximum response tokens (default: 2048).",
    )
    args = parser.parse_args(argv)
    if args.json:
        args.output_format = "json"
    return args


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

    try:
        image_ref = as_image_ref(args.image)
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    metadata = ""
    if not args.image.startswith(("http://", "https://", "data:")):
        metadata = describe_local_image(args.image)
    prompt_text = build_prompt(
        args.prompt, args.output_format, metadata
    )

    def call(client):
        return create_chat_completion(client, args, prompt_text, image_ref)

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

    content = response.choices[0].message.content or ""
    if not content:
        print("No content returned.", file=sys.stderr)
        return 1

    if args.output_format == "json":
        try:
            parsed = json.loads(strip_code_fences(content))
        except json.JSONDecodeError:
            print(content)
            print(
                "Warning: model did not return valid JSON.",
                file=sys.stderr,
            )
            return 1
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
        return 0

    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
