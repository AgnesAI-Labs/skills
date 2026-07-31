#!/usr/bin/env python3
"""Generate a video with Agnes AI and poll until completion.

Purpose
    Submit a text-to-video (or image-to-video with --image) task to
    the Agnes videos endpoint (model agnes-video-v2.0), poll the
    video_id status endpoint until the task completes, and print the
    final result JSON including the video URL. Nothing is written to
    disk unless --output is explicitly provided. Video creation and
    polling use direct HTTP requests (httpx) because the OpenAI SDK
    does not expose the video endpoint.

Dependencies
    pip install httpx

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
                    If the primary international route is unreachable
                    at the network level (DNS, TLS, connection
                    timeout), the creation request switches once to
                    https://apihub.agnes-ai.cn/v1. HTTP status errors
                    (400/401/403/422/429, ...) never trigger a route
                    change; keep the selected route and check the
                    request instead. See references/troubleshooting.md.

Minimal example
    export AGNES_API_KEY="your_api_key_here"
    python scripts/video_generate.py \
        --prompt "A cinematic wide shot of a futuristic city at night"

    # Download only when you ask for it:
    python scripts/video_generate.py --prompt "..." --output ./out/

Polling
    Creation returns a video_id. The script polls
    GET {service root}/agnesapi?video_id=<VIDEO_ID> (the service root
    is AGNES_BASE_URL without its /v1 suffix) until status is
    completed, failed, or cancelled. Poll every 10s or more; video
    rate limits are tight and aggressive polling can trigger 429.
    Transient poll errors (408/429/5xx and network failures) back off
    exponentially; anything else stops the script.

Error handling
    Exit codes: 0 success, 1 API or runtime failure (including
    timeout or failed/cancelled task), 2 missing AGNES_API_KEY or bad
    command-line usage. Diagnostics go to stderr; only the final JSON
    goes to stdout. The API key is never printed. Transient HTTP
    errors (408, 429, 500, 502, 503, 504, 520, 522, 524) are retried
    with exponential backoff before failing.

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
import time

import httpx

PRIMARY_URL = "https://apihub.agnes-ai.com/v1"
FALLBACK_URL = "https://apihub.agnes-ai.cn/v1"
DEFAULT_MODEL = "agnes-video-v2.0"
DEFAULT_WIDTH = 1152
DEFAULT_HEIGHT = 768
DEFAULT_DURATION = 5
DEFAULT_FRAME_RATE = 24
DEFAULT_POLL_INTERVAL = 10
DEFAULT_MAX_WAIT = 1800

MAX_VALID_FRAMES = 441
# Transient codes from references/troubleshooting.md and SKILL.md.
TRANSIENT_STATUS_CODES = (
    408, 429, 500, 502, 503, 504, 520, 522, 524,
)
HTTP_TIMEOUT = 60
DOWNLOAD_TIMEOUT = 300
RETRY_ATTEMPTS = 4
RETRY_BASE_DELAY = 2.0
MAX_CONSECUTIVE_POLL_FAILURES = 5

IMAGE_MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


class TransientStatusError(RuntimeError):
    """A retryable HTTP status code (see TRANSIENT_STATUS_CODES)."""

    def __init__(self, status_code, message=None):
        super().__init__(
            message or "HTTP {0}".format(status_code)
        )
        self.status_code = status_code


class ApiRequestError(RuntimeError):
    """A non-transient API error; carries the status code and body."""

    def __init__(self, status_code, body):
        super().__init__("HTTP {0}".format(status_code))
        self.status_code = status_code
        self.body = body


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


def nearest_valid_frames(count):
    """Snap a frame count down to the 8n+1 grid, capped at 441."""
    count = min(count, MAX_VALID_FRAMES)
    steps = max((count - 1) // 8, 0)
    return 8 * steps + 1


def resolve_num_frames(args):
    """Compute the num_frames payload field from CLI arguments."""
    if args.num_frames is not None:
        return nearest_valid_frames(args.num_frames)
    raw = int(args.duration * args.frame_rate + 0.5)
    return nearest_valid_frames(raw)


def service_root(base_url):
    """Derive the non-/v1 service root used for status polling."""
    if base_url.endswith("/v1"):
        return base_url[: -len("/v1")]
    return base_url


def http_request(
    method, url, api_key, params=None, json_body=None,
    attempts=RETRY_ATTEMPTS,
):
    """Direct HTTP request with exponential backoff.

    Retries the transient status codes listed in SKILL.md and
    references/troubleshooting.md (408, 429, 500, 502, 503, 504,
    520, 522, 524). Network-level failures (DNS, TLS, connection
    timeout) raise httpx.TransportError immediately so callers can
    switch routes or surface them. Other responses are returned
    as-is for the caller to inspect.
    """
    headers = {"Authorization": "Bearer " + api_key}
    delay = RETRY_BASE_DELAY
    for attempt in range(1, attempts + 1):
        response = httpx.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_body,
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
        )
        if response.status_code not in TRANSIENT_STATUS_CODES:
            return response
        if attempt == attempts:
            raise TransientStatusError(
                response.status_code,
                "HTTP {0} persisted after {1} attempts".format(
                    response.status_code, attempts
                ),
            )
        print(
            "Transient HTTP {0}; retrying in {1:.0f}s...".format(
                response.status_code, delay
            ),
            file=sys.stderr,
        )
        time.sleep(delay)
        delay = min(delay * 2, 60)


def create_video_task(base_url, api_key, payload):
    """Create the video task via POST /videos (direct HTTP).

    Transient status codes are retried with backoff. A network-level
    failure on the international primary switches once to the
    alternate international route; HTTP status errors never switch
    routes.
    """
    def attempt(url_base):
        response = http_request(
            "POST",
            url_base + "/videos",
            api_key,
            json_body=payload,
        )
        if response.status_code >= 400:
            raise ApiRequestError(
                response.status_code, response.text
            )
        return response.json()

    try:
        return attempt(base_url)
    except httpx.TransportError:
        if base_url != PRIMARY_URL:
            raise
        print(
            "Primary route unreachable; retrying with {0}".format(
                FALLBACK_URL
            ),
            file=sys.stderr,
        )
        return attempt(FALLBACK_URL)


def poll_once(base_url, api_key, video_id):
    """Fetch the video status document once (the loop owns retries).

    Transient status codes raise TransientStatusError and network
    failures raise httpx.TransportError; poll_until_done backs off
    and retries both. Other HTTP errors are fatal.
    """
    response = httpx.request(
        "GET",
        service_root(base_url) + "/agnesapi",
        headers={"Authorization": "Bearer " + api_key},
        params={"video_id": video_id},
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
    )
    if response.status_code in TRANSIENT_STATUS_CODES:
        raise TransientStatusError(response.status_code)
    if response.status_code >= 400:
        raise RuntimeError(
            "Status poll failed: HTTP {0}".format(
                response.status_code
            )
        )
    return response.json()


def poll_until_done(base_url, api_key, video_id, args):
    """Poll the status endpoint until a terminal state; return it."""
    deadline = time.monotonic() + args.max_wait
    consecutive_failures = 0
    while True:
        if time.monotonic() > deadline:
            raise RuntimeError(
                "Timed out after {0}s waiting for video.".format(
                    args.max_wait
                )
            )
        try:
            status_doc = poll_once(base_url, api_key, video_id)
            consecutive_failures = 0
        except TransientStatusError as exc:
            consecutive_failures += 1
            print(
                "Poll returned HTTP {0}; backing off.".format(
                    exc.status_code
                ),
                file=sys.stderr,
            )
        except httpx.TransportError as exc:
            consecutive_failures += 1
            print(
                "Poll network error: {0}; backing off.".format(exc),
                file=sys.stderr,
            )

        if consecutive_failures >= MAX_CONSECUTIVE_POLL_FAILURES:
            raise RuntimeError(
                "Status polling failed {0} times in a row.".format(
                    consecutive_failures
                )
            )

        if consecutive_failures == 0:
            status = status_doc.get("status") or "unknown"
            progress = status_doc.get("progress", 0)
            print(
                "Status: {0} | Progress: {1}%".format(
                    status, progress
                ),
                file=sys.stderr,
            )
            if status == "completed":
                return status_doc
            if status in ("failed", "cancelled"):
                raise RuntimeError(
                    "Video generation {0}: {1}".format(
                        status,
                        json.dumps(status_doc, ensure_ascii=False),
                    )
                )

        backoff = min(
            args.poll_interval
            * (2 ** max(consecutive_failures - 1, 0)),
            60,
        )
        time.sleep(backoff)


def final_video_url(status_doc):
    """Extract the result URL from a completed status document."""
    return (
        status_doc.get("remixed_from_video_id")
        or status_doc.get("url")
        or status_doc.get("video_url")
    )


def download_video(url, destination):
    """Download the finished video; return the written file path."""
    if os.path.isdir(destination) or destination.endswith(os.sep):
        os.makedirs(destination, exist_ok=True)
        path = os.path.join(
            destination,
            "agnes_video_{0}.mp4".format(int(time.time())),
        )
    else:
        parent = os.path.dirname(os.path.abspath(destination))
        os.makedirs(parent, exist_ok=True)
        path = destination
    with httpx.stream(
        "GET", url, timeout=DOWNLOAD_TIMEOUT, follow_redirects=True
    ) as response:
        response.raise_for_status()
        with open(path, "wb") as handle:
            for chunk in response.iter_bytes():
                handle.write(chunk)
    return path


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a video with Agnes AI and poll for it."
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Video generation prompt.",
    )
    parser.add_argument(
        "--image",
        default=None,
        help="Starting image path or URL for image-to-video.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help="Output width (default: 1152).",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help="Output height (default: 768).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=DEFAULT_DURATION,
        help=(
            "Target duration in seconds, used to derive num_frames "
            "(default: 5). Ignored when --num-frames is set."
        ),
    )
    parser.add_argument(
        "--frame-rate",
        type=int,
        default=DEFAULT_FRAME_RATE,
        help="Frames per second (default: 24).",
    )
    parser.add_argument(
        "--num-frames",
        type=int,
        default=None,
        help=(
            "Override duration; snapped down to the 8n+1 grid "
            "(max 441). Snapping down keeps generation fast and "
            "reliable."
        ),
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model name (default: agnes-video-v2.0).",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL,
        help="Seconds between status checks (default: 10).",
    )
    parser.add_argument(
        "--max-wait",
        type=float,
        default=DEFAULT_MAX_WAIT,
        help="Maximum seconds to wait (default: 1800).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "Download the finished video to this path (directory or "
            "file). Nothing is written to disk unless this is set."
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

    num_frames = resolve_num_frames(args)
    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "width": args.width,
        "height": args.height,
        "num_frames": num_frames,
        "frame_rate": args.frame_rate,
    }
    if args.image:
        try:
            payload["image"] = as_image_ref(args.image)
        except OSError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    print(
        "Creating video task (num_frames={0})...".format(num_frames),
        file=sys.stderr,
    )
    try:
        create_doc = create_video_task(base_url, api_key, payload)
    except ApiRequestError as exc:
        print(
            "API error: HTTP {0}".format(exc.status_code),
            file=sys.stderr,
        )
        print(exc.body, file=sys.stderr)
        return 1
    except TransientStatusError as exc:
        print("API error: {0}".format(exc), file=sys.stderr)
        return 1
    except httpx.TransportError as exc:
        print("Connection failed: {0}".format(exc), file=sys.stderr)
        return 1

    video_id = create_doc.get("video_id")
    if not video_id:
        print(
            "Failed to create video task. Response:", file=sys.stderr
        )
        print(
            json.dumps(create_doc, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1
    print(
        "Task created: {0} (video_id: {1})".format(
            create_doc.get("task_id", ""), video_id
        ),
        file=sys.stderr,
    )

    try:
        status_doc = poll_until_done(
            base_url, api_key, video_id, args
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    video_url = final_video_url(status_doc)
    saved_file = None
    if args.output:
        if not video_url:
            print(
                "Task completed but no video URL was returned.",
                file=sys.stderr,
            )
            return 1
        try:
            saved_file = download_video(video_url, args.output)
        except (httpx.HTTPError, OSError) as exc:
            print(
                "Download failed: {0}".format(exc), file=sys.stderr
            )
            return 1
        print("Saved {0}".format(saved_file), file=sys.stderr)

    result = {
        "status": status_doc.get("status"),
        "video_id": video_id,
        "video_url": video_url,
        "saved_file": saved_file,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
