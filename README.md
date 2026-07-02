# Agnes AI Skills

Official skill repository for Agnes AI model integration.

This repository provides a reusable Codex skill for integrating Agnes AI text, image, video, and agent models through the OpenAI-compatible API gateway.

## Available Skills

| Skill | Purpose |
| --- | --- |
| [`agnes-ai-models`](./agnes-ai-models) | Integrate Agnes AI text, image, video, and agent workflows. |

## Model Coverage

| Model | Type | Primary use |
| --- | --- | --- |
| `agnes-2.0-flash` | Text and vision-language | Chat, coding, reasoning, streaming, tools, and image understanding |
| `agnes-image-2.0-flash` | Image generation | Fast text-to-image and image-to-image generation |
| `agnes-image-2.1-flash` | Image generation | Higher quality image generation and editing |
| `agnes-video-v2.0` | Video generation | Text-to-video, image-to-video, and video result polling |

## Requirements

Before using the skill, each user must:

1. Register an Agnes Platform account: https://platform.agnes-ai.com/
2. Apply for an Agnes API key in the platform.
3. Store the key locally as an environment variable:

```bash
export AGNES_API_KEY="your_api_key_here"
```

Do not commit API keys, bearer tokens, `.env` files, screenshots containing secrets, or private customer data.

## Quick Start

Copy or install the `agnes-ai-models` skill into your Codex skills directory, then ask Codex to use it for Agnes AI API integration tasks.

Example prompt:

```text
Use the Agnes AI Models skill to create a Python example for agnes-2.0-flash.
```

## What The Skill Covers

- OpenAI-compatible chat completions
- Streaming responses
- Image generation with `agnes-image-2.0-flash` and `agnes-image-2.1-flash`
- Video generation with `agnes-video-v2.0` and `video_id` polling
- Tool-calling style agent workflows
- Common API errors and debugging checklists
- Token Plan and RPM reference notes

## Official Links

- Website: https://agnes-ai.com/
- Docs: https://agnes-ai.com/doc/overview
- Platform: https://platform.agnes-ai.com/
- API base URL: `https://apihub.agnes-ai.com/v1`

## Language

- [English](./README.md)
- [简体中文](./README.zh-CN.md)
