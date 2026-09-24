---
name: agnes-ai-models
description: Agnes AI model integration skill for OpenAI-compatible text, image, video, and agent workflows. Use when Codex needs to configure Agnes AI API access, select or document Agnes models including agnes-2.5-flash, agnes-image-2.5-flash, agnes-video-2.5, and agnes-video-2.5-flash, write Python/Node/curl examples, debug common API errors, poll video results with video_id, adapt OpenAI-compatible clients to the Agnes API gateway, or prepare guidance for other agent software such as OpenClaw, Hermes, Manus, and custom agents.
---

# Agnes AI Models

Use this skill to help developers integrate Agnes AI models through the OpenAI-compatible API gateway.

Users must register at `https://platform.agnes-ai.com/` and apply for an API key before making requests. Never invent, expose, or ask the user to paste secrets into public files.

## Core Defaults

- API base URL: `https://apihub.agnes-ai.com/v1`
- Optional base URL override: `AGNES_BASE_URL`
- API key env var: `AGNES_API_KEY`
- Auth header: `Authorization: Bearer $AGNES_API_KEY`
- Official docs: `https://agnes-ai.com/en/docs/overview`
- Platform: `https://platform.agnes-ai.com/`

## Regional Endpoint Routing

Choose the service route before configuring a client. Do not automatically rotate an API key across services after an authentication or quota error.

| Service route | Base URL | When to use it |
| --- | --- | --- |
| International service (primary) | `https://apihub.agnes-ai.com/v1` | Default route for the international service |
| International service (alternate) | `https://apihub.agnes-ai.cn/v1` | Only when the primary route has a network, DNS, TLS, or connection-timeout failure |
| China service | `https://api.agnes-ai.cn/v1` | Use for the China service |

If the base URL cannot connect, confirm `/v1` is present, identify the intended service, and test at most one minimal alternate-route request. Do not switch routes to solve `400`, `401`, `403`, `422`, or `429` responses.

## Model Selection

Use these defaults unless the user specifies a different model:

| Workflow | Model | Endpoint |
| --- | --- | --- |
| Chat, coding, reasoning, tools, streaming, vision input | `agnes-2.5-flash` | `POST /v1/chat/completions` |
| Image generation, editing, and multi-image composition | `agnes-image-2.5-flash` | `POST /v1/images/generations` |
| Text-to-video, keyframes, and multimodal references | `agnes-video-2.5` | `POST /v1/videos` |
| Fast 720P text-to-video and reference generation | `agnes-video-2.5-flash` | `POST /v1/videos` |

For detailed model notes, read `references/model_catalog.md`.

For OpenClaw, Hermes, Manus, or other non-Codex agent setup, read `references/agent_compatibility.md`.

## Integration Workflow

1. Confirm the user has an Agnes Platform account and API key for the selected service.
2. Store the key in `AGNES_API_KEY`; do not hardcode it.
3. Set `AGNES_BASE_URL` when using an alternate or China route.
4. Use the OpenAI SDK when the workflow is chat or image generation.
5. Use direct HTTP requests for video creation and polling if the SDK does not expose the video endpoint.
6. For image-to-image or multi-image requests, pass input images in `extra_body.image` (public URLs or Data URI Base64). Put `response_format` in `extra_body`, not at the top level.
7. For video results, always poll with the returned `video_id` and the model name:

```text
GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>&model_name=<MODEL_ID>
```

8. Treat the video response's top-level `status` and `url` as the source of truth. Stop on `completed` or `failed`; use backoff for `429` responses.
9. Add retries with exponential backoff for `408`, `429`, `500`, `502`, `503`, `504`, `520`, `522`, and `524`.
10. When writing public docs or examples, state that limits and model availability may change and users should confirm production-critical values in official docs or the platform console.

## Image Generation Pattern

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["AGNES_API_KEY"],
    base_url=os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1"),
)

result = client.images.generate(
    model="agnes-image-2.5-flash",
    prompt="A cinematic product hero image for a desktop monitor wallpaper",
    size="2K",
    extra_body={"ratio": "16:9", "response_format": "url"},
)
print(result.data[0].url)
```

Use `size` tiers `1K`, `2K`, `3K`, or `4K` with a supported `ratio`. For image-to-image and multi-image composition, add `extra_body={"image": ["<PUBLIC_URL_OR_DATA_URI>"]}`. Do not add a legacy `tags` field.

## Video Generation Pattern

Create a video with `agnes-video-2.5` or `agnes-video-2.5-flash` at `POST /v1/videos`, then poll `/agnesapi` with both `video_id` and `model_name`. The base model supports `720P`, `1080P`, `1K`, and `2K`; Flash is limited to `720P` and does not accept reference videos.

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

## Optional Smoke Test

Use `scripts/smoke_chat.py` to test whether `AGNES_API_KEY` and the chat endpoint are configured correctly:

```bash
python scripts/smoke_chat.py
```
