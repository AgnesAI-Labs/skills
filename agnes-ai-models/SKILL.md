---
name: agnes-ai-models
description: Agnes AI model integration skill for OpenAI-compatible text, image, video, and agent workflows. Use when Codex needs to configure Agnes AI API access, select or document Agnes models including agnes-2.0-flash, agnes-image-2.0-flash, agnes-image-2.1-flash, and agnes-video-v2.0, write Python/Node/curl examples, debug common API errors, poll video results with video_id, adapt OpenAI-compatible clients to the Agnes API gateway, or prepare guidance for other agent software such as OpenClaw, Hermes, Manus, and custom agents.
---

# Agnes AI Models

Use this skill to help developers integrate Agnes AI models through the OpenAI-compatible API gateway.

Users must register at `https://platform.agnes-ai.com/` and apply for an API key before making requests. Never invent, expose, or ask the user to paste secrets into public files.

## Core Defaults

- API base URL: `https://apihub.agnes-ai.com/v1`
- API key env var: `AGNES_API_KEY`
- Auth header: `Authorization: Bearer $AGNES_API_KEY`
- Official docs: `https://agnes-ai.com/doc/overview`
- Platform: `https://platform.agnes-ai.com/`

## Model Selection

Use these defaults unless the user specifies a different model:

| Workflow | Model | Endpoint |
| --- | --- | --- |
| Chat, coding, reasoning, tools, streaming, vision input | `agnes-2.0-flash` | `POST /v1/chat/completions` |
| Image generation and editing | `agnes-image-2.1-flash` | `POST /v1/images/generations` |
| Fast image generation | `agnes-image-2.0-flash` | `POST /v1/images/generations` |
| Text-to-video and image-to-video | `agnes-video-v2.0` | `POST /v1/videos` |

For detailed model notes, read `references/model_catalog.md`.

For OpenClaw, Hermes, Manus, or other non-Codex agent setup, read `references/agent_compatibility.md`.

## Integration Workflow

1. Confirm the user has an Agnes Platform account and API key.
2. Store the key in `AGNES_API_KEY`; do not hardcode it.
3. Use the OpenAI SDK when the workflow is chat or image generation.
4. Use direct HTTP requests for video creation and polling if the SDK does not expose the video endpoint.
5. For video results, poll with:

```text
GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>
```

6. Add retries with exponential backoff for `408`, `429`, `500`, `502`, `503`, `504`, `520`, `522`, and `524`.
7. When writing public docs or examples, state that limits and model availability may change and users should confirm production-critical values in official docs or the platform console.

## Minimal Python Pattern

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["AGNES_API_KEY"],
    base_url="https://apihub.agnes-ai.com/v1",
)

response = client.chat.completions.create(
    model="agnes-2.0-flash",
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
