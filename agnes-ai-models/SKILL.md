---
name: agnes-ai-models
description: Agnes AI model integration skill for OpenAI-compatible text, image, video, and agent workflows. Use when Codex needs to configure Agnes AI API access, select or document Agnes models including agnes-2.5-flash, agnes-image-2.1-flash, and agnes-video-v2.0, write Python/Node/curl examples, debug common API errors, poll video results with video_id, adapt OpenAI-compatible clients to the Agnes API gateway, or prepare guidance for other agent software such as OpenClaw, Hermes, Manus, and custom agents.
---

# Agnes AI Models

Use this skill to help developers integrate Agnes AI models through the OpenAI-compatible API gateway.

Users must register at `https://platform.agnes-ai.com/` and apply for an API key before making requests. Never invent, expose, or ask the user to paste secrets into public files.

## Core Defaults

- Default API base URL (International service): `https://apihub.agnes-ai.com/v1`
- API key env var: `AGNES_API_KEY`
- Auth header: `Authorization: Bearer $AGNES_API_KEY`
- Official docs: `https://agnes-ai.com/doc/overview`
- Platform: `https://platform.agnes-ai.com/`

## Regional Endpoint Routing

Choose the service route before configuring a client or proposing a fallback. Do not automatically rotate an API key across services after an authentication or quota error.

| Service route | Base URL | When to use it |
| --- | --- | --- |
| International service (primary) | `https://apihub.agnes-ai.com/v1` | Default route for the international service. |
| International service (alternate) | `https://apihub.agnes-ai.cn/v1` | Use when the international primary route has a network, DNS, TLS, or connection-timeout failure. |
| China service | `https://api.agnes-ai.cn/v1` | Use for the China service. |

When a user reports that the Base URL cannot connect:

1. Confirm that the URL includes `/v1` and that the client is not appending `/v1` twice.
2. Ask which service the user is using: International or China.
3. For the International service, start with `https://apihub.agnes-ai.com/v1`. If that route is unreachable, test `https://apihub.agnes-ai.cn/v1` with one minimal request and keep the reachable route.
4. For the China service, configure `https://api.agnes-ai.cn/v1`.
5. Set the selected URL through `AGNES_BASE_URL` or the agent's custom OpenAI-compatible provider setting.
6. Do not switch routes to solve `400`, `401`, `403`, `422`, or `429` responses. Those require request, account, API key, permission, or rate-limit checks for the selected service.

## Model Selection

Use these defaults unless the user specifies a different model:

| Workflow | Model | Endpoint |
| --- | --- | --- |
| Chat, coding, reasoning, tools, streaming, vision input | `agnes-2.5-flash` | `POST /v1/chat/completions` |
| Image generation and editing | `agnes-image-2.1-flash` | `POST /v1/images/generations` |
| Text-to-video and image-to-video | `agnes-video-v2.0` | `POST /v1/videos` |

For detailed model notes, read `references/model_catalog.md`.

For OpenClaw, Hermes, Manus, or other non-Codex agent setup, read `references/agent_compatibility.md`.

## Integration Workflow

1. Confirm the user has an Agnes Platform account and API key for the selected service.
2. Select the regional endpoint using the routing rules above and save it as `AGNES_BASE_URL` when the client supports environment-based configuration.
3. Store the key in `AGNES_API_KEY`; do not hardcode it.
4. Use the OpenAI SDK when the workflow is chat or image generation.
5. Use direct HTTP requests for video creation and polling if the SDK does not expose the video endpoint.
6. For video results, poll with:

```text
GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>
```

7. Add retries with exponential backoff for `408`, `429`, `500`, `502`, `503`, `504`, `520`, `522`, and `524`.
8. When writing public docs or examples, state that limits and model availability may change and users should confirm production-critical values in official docs or the platform console.

## Minimal Python Pattern

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["AGNES_API_KEY"],
    base_url=os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1"),
)

response = client.chat.completions.create(
    model="agnes-2.5-flash",
    messages=[{"role": "user", "content": "Write a short intro to Agnes AI."}],
    stream=True,
)

for chunk in response:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="")
```

## Debugging

For common errors, read `references/troubleshooting.md`.

Required issue/debug fields:

- model
- endpoint
- SDK or client
- sanitized request body
- timestamp and request ID if available
- status code and response body
- expected behavior
- actual behavior

Never include API keys, bearer tokens, private logs, or customer data.

## Runnable Helper Scripts

Ready-to-run scripts for each workflow. All scripts require `AGNES_API_KEY`
and support `AGNES_BASE_URL`. Run `--help` on any script for full usage.

| Script | Workflow | Model |
| --- | --- | --- |
| `scripts/image_understand.py` | Analyze a local image or URL | `agnes-2.5-flash` |
| `scripts/image_generate.py` | Generate or edit images | `agnes-image-2.1-flash` |
| `scripts/video_understand.py` | Analyze a video via sampled frames (requires ffmpeg) | `agnes-2.5-flash` |
| `scripts/video_generate.py` | Generate video and poll for result | `agnes-video-v2.0` |

### Quick examples

```bash
# Image understanding
python scripts/image_understand.py --image photo.jpg --prompt "Describe this image."

# Image generation (prints JSON; add --output ./out/ to save)
python scripts/image_generate.py --prompt "A product photo of headphones" --size 1024x768

# Video understanding (requires ffmpeg)
python scripts/video_understand.py --video clip.mp4 --prompt "Summarize this video."

# Video generation (prints JSON; add --output ./out/ to download)
python scripts/video_generate.py --prompt "A cinematic shot of a city at night"
```

All scripts support `--format text|structured|json` (understand scripts) and
`--output <path>` (generate scripts). Nothing is written to disk unless
`--output` is explicitly provided.

For prompt templates and structured-output schemas, read
`references/prompt-templates.md`.

## Prompt Enhancement

When composing prompts for the user, consult `references/prompt-components.md`:

1. If the request is clear (subject + style + mood) → assemble the prompt directly using the formula and component tables. Do not ask questions.
2. If the request has a subject but missing style/mood → suggest 2–3 component combinations and let the user pick.
3. If the request is vague → ask up to 3 focused questions (subject, style, use case), then assemble.
4. Always append relevant negative prompts from the reference file.
5. Translate non-English input to English for the final prompt (models respond better to English).
6. Always return both the saved file path AND the API URL to the user.

## Optional Smoke Test

Use `scripts/smoke_chat.py` to test whether `AGNES_API_KEY` and the selected chat endpoint are configured correctly. Set `AGNES_BASE_URL` first when using the international alternate route or the China service:

```bash
python scripts/smoke_chat.py
```
