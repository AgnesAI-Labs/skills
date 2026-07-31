#!/usr/bin/env python3
"""Analyze a video with Agnes AI by sampling frames with ffmpeg.

Purpose
    Sample evenly spaced frames from a video (local file or public URL),
    send them to the Agnes chat completions endpoint (model
    agnes-2.5-flash) as images, and print the analysis. Supports plain
    text, structured markdown, and JSON output.

Dependencies
    pip install openai
    (httpx ships with openai and is used to fetch URL inputs)
    ffmpeg and ffprobe on PATH (e.g. `apt install ffmpeg` or
    `brew install ffmpeg`).

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
    python scripts/video_understand.py \
        --video clip.mp4 \
        --prompt "Summarize what happens in this video."

Error handling
    Exit codes: 0 success, 1 API or runtime failure (including missing
    ffmpeg or unreadable video), 2 missing AGNES_API_KEY or bad
    command-line usage. Diagnostics go to stderr; only the model reply
    goes to stdout. The API key is never printed.
    Transient HTTP errors (408, 429, 500, 502, 503, 504, 520, 522,
    524) are retried with exponential backoff before failing.

Notes
    A --video URL is fetched into a temporary directory, and sampled
    frames are written there too; the directory is removed on exit.
    Nothing is written outside it: the script produces no output
    files, so no explicit download step exists.

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
import tempfile

import httpx
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
)

PRIMARY_URL = "https://apihub.agnes-ai.com/v1"
FALLBACK_URL = "https://apihub.agnes-ai.cn/v1"
DEFAULT_MODEL = "agnes-2.5-flash"
DEFAULT_FRAMES = 5
DEFAULT_MAX_WIDTH = 512
DEFAULT_MAX_TOKENS = 2048

STRUCTURED_SUFFIX = (
    "\n\nProvide a structured analysis with the following sections:\n"
    "- Summary (one sentence)\n"
    "- Keyframes analyzed (describe what happens at each extracted "
    "timestamp)\n"
    "- Scene-by-scene description\n"
    "- Settings\n"
    "- Characters / actions\n"
    "- Camera movement\n"
    "- Visual style\n"
    "- Mood / tone\n"
    "- Audio description (if inferable)\n"
    "- Metadata (duration, resolution, frame rate, format)"
)

JSON_SUFFIX = (
    "\n\nReturn the result as valid JSON matching this schema:\n"
    "{\n"
    '  "summary": "string",\n'
    '  "keyframes": [{"timestamp": "00:00:00.000", '
    '"description": "string"}],\n'
    '  "scenes": [{"start": "00:00", "end": "00:05", '
    '"description": "string"}],\n'
    '  "settings": ["string"],\n'
    '  "characters_actions": ["string"],\n'
    '  "camera_movement": "string",\n'
    '  "visual_style": "string",\n'
    '  "mood": "string",\n'
    '  "audio_description": "string",\n'
    '  "metadata": {"duration_seconds": 0, "resolution": "string", '
    '"frame_rate": 0, "format": "string"}\n'
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


def require_ffmpeg_tools():
    """Exit early with a clear message when ffmpeg tools are missing."""
    missing = [
        tool
        for tool in ("ffmpeg", "ffprobe")
        if shutil.which(tool) is None
    ]
    if missing:
        print(
            "{0} required on PATH. Install ffmpeg and try again.".format(
                ", ".join(missing)
            ),
            file=sys.stderr,
        )
        raise SystemExit(1)


def run_ffmpeg(argv):
    """Run an ffmpeg/ffprobe command; raise RuntimeError with output."""
    try:
        completed = subprocess.run(
            argv, capture_output=True, text=True, check=True
        )
    except OSError as exc:
        raise RuntimeError("Failed to run {0}: {1}".format(argv[0], exc))
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip()
        raise RuntimeError(
            "{0} failed: {1}".format(argv[0], detail or exc)
        )
    return completed.stdout


def probe_duration(video_path):
    """Return the video duration in seconds."""
    output = run_ffmpeg(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
    ).strip()
    try:
        duration = float(output)
    except ValueError:
        raise RuntimeError(
            "Could not read video duration from ffprobe."
        )
    if duration <= 0:
        raise RuntimeError("Video duration is zero or negative.")
    return duration


def probe_metadata(video_path):
    """Best-effort one-line metadata string for the prompt."""
    try:
        duration = run_ffmpeg(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ]
        ).strip()
        width = run_ffmpeg(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ]
        ).strip()
        height = run_ffmpeg(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=height",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ]
        ).strip()
        frame_rate = run_ffmpeg(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ]
        ).strip()
    except RuntimeError:
        return ""
    return (
        "Video metadata: duration={0}s, resolution={1}x{2}, "
        "frame_rate={3}.".format(duration, width, height, frame_rate)
    )


def format_time(seconds):
    """Format seconds as HH:MM:SS.mmm for keyframe labels."""
    hours = int(seconds // 3600)
    minutes = int((seconds - hours * 3600) // 60)
    secs = seconds - hours * 3600 - minutes * 60
    return "{0:02d}:{1:02d}:{2:06.3f}".format(hours, minutes, secs)


def frame_times(duration, count):
    """Evenly spaced sample times strictly inside (0, duration)."""
    return [
        duration * (i + 1) / (count + 1) for i in range(count)
    ]


def extract_frame(video_path, seconds, max_width, out_path):
    """Extract one scaled JPEG frame at the given timestamp."""
    run_ffmpeg(
        [
            "ffmpeg",
            "-v", "error",
            "-ss", "{0:.6f}".format(seconds),
            "-i", video_path,
            "-vf", "scale={0}:-2".format(max_width),
            "-vframes", "1",
            "-q:v", "2",
            out_path,
        ]
    )


def sample_frames(video_path, duration, args, workdir):
    """Extract frames; return (labels, base64 data URL parts)."""
    labels = []
    image_parts = []
    times = frame_times(duration, args.frames)
    for index, seconds in enumerate(times):
        out_path = os.path.join(
            workdir, "frame_{0:03d}.jpg".format(index)
        )
        extract_frame(video_path, seconds, args.max_width, out_path)
        with open(out_path, "rb") as handle:
            encoded = base64.b64encode(handle.read()).decode("ascii")
        labels.append(format_time(seconds))
        image_parts.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": "data:image/jpeg;base64," + encoded,
                },
            }
        )
    return labels, image_parts


def build_prompt(user_prompt, output_format, metadata, keyframes):
    """Compose the full instruction for the requested output format."""
    header = "{0}\n\nExtracted keyframes at: {1}".format(
        user_prompt, keyframes
    )
    if output_format == "text":
        return header
    if output_format == "json":
        suffix = JSON_SUFFIX
    else:
        suffix = STRUCTURED_SUFFIX
    if metadata:
        return header + suffix + "\n\n" + metadata
    return header + suffix


def strip_code_fences(text):
    """Remove optional ```json fences models sometimes add."""
    match = re.search(r"```(?:json)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    return match.group(1) if match else text


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


def resolve_local_video(video, workdir):
    """Return a local path for video, fetching URLs into workdir.

    URL inputs are streamed into the temporary workdir (removed on
    exit); nothing is written anywhere else.
    """
    if video.startswith(("http://", "https://")):
        local_path = os.path.join(workdir, "video.mp4")
        print("Fetching video URL to temporary directory...",
              file=sys.stderr)
        with httpx.stream(
            "GET", video, timeout=120, follow_redirects=True
        ) as response:
            response.raise_for_status()
            with open(local_path, "wb") as handle:
                for chunk in response.iter_bytes():
                    handle.write(chunk)
        return local_path
    if not os.path.isfile(video):
        raise FileNotFoundError(
            "Video file not found: {0}".format(video)
        )
    return video


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Analyze a video with Agnes AI by sampling frames "
            "(requires ffmpeg)."
        )
    )
    parser.add_argument(
        "--video",
        required=True,
        help=(
            "Local video path or publicly accessible URL. URL inputs "
            "are fetched into a temporary directory that is removed "
            "on exit."
        ),
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Analysis instruction for the model.",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=DEFAULT_FRAMES,
        help="Number of frames to sample (default: 5).",
    )
    parser.add_argument(
        "--max-width",
        type=int,
        default=DEFAULT_MAX_WIDTH,
        help="Resize frames to this width to save tokens (default: 512).",
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
    if args.frames < 1:
        parser.error("--frames must be >= 1")
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

    require_ffmpeg_tools()

    base_url = os.environ.get("AGNES_BASE_URL", PRIMARY_URL).rstrip("/")
    print("Using AGNES_BASE_URL={0}".format(base_url), file=sys.stderr)

    with tempfile.TemporaryDirectory() as workdir:
        try:
            video_path = resolve_local_video(args.video, workdir)
            duration = probe_duration(video_path)
            print(
                "Extracting {0} frames across full video "
                "({1:.1f}s)...".format(args.frames, duration),
                file=sys.stderr,
            )
            metadata = probe_metadata(video_path)
            labels, image_parts = sample_frames(
                video_path, duration, args, workdir
            )
        except (RuntimeError, OSError, httpx.HTTPError) as exc:
            print(str(exc), file=sys.stderr)
            return 1

        keyframes = ", ".join(labels)
        prompt_text = build_prompt(
            args.prompt, args.output_format, metadata, keyframes
        )

        def call(client):
            return client.chat.completions.create(
                model=args.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                        ]
                        + image_parts,
                    }
                ],
                max_tokens=args.max_tokens,
            )

        try:
            response = run_with_route_fallback(base_url, api_key, call)
        except APIStatusError as exc:
            print(
                "API error: {0} {1}".format(
                    exc.status_code, exc.message
                ),
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

    print("Extracted keyframes at: {0}".format(keyframes))
    print()
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
