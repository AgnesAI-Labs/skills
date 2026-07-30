# Agnes AI Skills

<p align="center">
  <a href="./README.md"><img alt="Language: English" src="https://img.shields.io/badge/LANGUAGE-ENGLISH-0969DA?style=for-the-badge&labelColor=555555"></a>
  <a href="./README.zh-CN.md"><img alt="Language: Simplified Chinese" src="https://img.shields.io/badge/LANGUAGE-%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-1F883D?style=for-the-badge&labelColor=555555"></a>
</p>

Official skill repository for Agnes AI model integration.

This repository provides a reusable Codex skill for integrating Agnes AI text, image, video, and agent models through the OpenAI-compatible API gateway.

## Available Skills

| Skill | Purpose |
| --- | --- |
| [`agnes-ai-models`](./agnes-ai-models) | Integrate Agnes AI text, image, video, and agent workflows. |

## Install From GitHub

Codex users can install the skill from this GitHub repository by targeting the skill directory:

```bash
python /path/to/install-skill-from-github.py \
  --repo AgnesAI-Labs/skills \
  --path agnes-ai-models
```

If your Codex environment supports URL-based installation, use:

```bash
python /path/to/install-skill-from-github.py \
  --url https://github.com/AgnesAI-Labs/skills/tree/main/agnes-ai-models
```

Restart Codex after installation so the skill is discovered.

## Model Coverage

| Model | Type | Primary use |
| --- | --- | --- |
| `agnes-2.5-flash` | Text and vision-language | Chat, coding, reasoning, streaming, tools, and image understanding |
| `agnes-image-2.1-flash` | Image generation | Higher quality image generation and editing |
| `agnes-video-v2.0` | Video generation | Text-to-video, image-to-video, and video result polling |

## Agent Compatibility

This repository is packaged as a Codex Skill, but the skill content can also be used by other agent software such as OpenClaw, Hermes, Manus, and custom agents.

For non-Codex agents, use the files in [`agnes-ai-models`](./agnes-ai-models) as integration instructions:

- Read [`SKILL.md`](./agnes-ai-models/SKILL.md) for the main workflow.
- Use [`references/model_catalog.md`](./agnes-ai-models/references/model_catalog.md) for model names, endpoints, RPM notes, and Token Plan notes.
- Use [`references/troubleshooting.md`](./agnes-ai-models/references/troubleshooting.md) for common API errors.
- Use [`references/agent_compatibility.md`](./agnes-ai-models/references/agent_compatibility.md) for OpenClaw, Hermes, WorkBuddy, Manus, and generic agent setup guidance.

Agnes AI uses an OpenAI-compatible API gateway. Most agent frameworks that support custom OpenAI-compatible providers can use Agnes models by setting the Agnes base URL, API key, and model name.

## Requirements

Before using the skill, each user must:

1. Register an Agnes Platform account: https://platform.agnes-ai.com/
2. Apply for an Agnes API key in the platform.
3. Store the key locally as an environment variable:

```bash
export AGNES_API_KEY="your_api_key_here"
```

Do not commit API keys, bearer tokens, `.env` files, screenshots containing secrets, or private customer data.

## Regional Endpoint Routing

Select the service route before configuring a client:

| Service route | Base URL |
| --- | --- |
| International service (primary) | `https://apihub.agnes-ai.com/v1` |
| International service (alternate) | `https://apihub.agnes-ai.cn/v1` |
| China service | `https://api.agnes-ai.cn/v1` |

For the International service, start with the primary route. If it has a network, DNS, TLS, or connection-timeout failure, test the alternate route with one minimal request and keep the reachable route. For the China service, use the China service route. Do not switch routes to resolve `400`, `401`, `403`, `422`, or `429` responses.

Set the selected URL in an environment variable when supported:

```bash
export AGNES_BASE_URL="https://apihub.agnes-ai.com/v1"
```

## Quick Start

Copy or install the `agnes-ai-models` skill into your Codex skills directory, or link the GitHub skill directory from another agent that supports external instructions. Then ask the agent to use it for Agnes AI API integration tasks.

Example prompt:

```text
Use the Agnes AI Models skill to create a Python example for agnes-2.5-flash.
```

## What The Skill Covers

- OpenAI-compatible chat completions
- Streaming responses
- Image generation with `agnes-image-2.1-flash`
- Video generation with `agnes-video-v2.0` and `video_id` polling
- Tool-calling style agent workflows
- Common API errors and debugging checklists
- Token Plan and RPM reference notes

## Official Links

- Website: https://agnes-ai.com/
- Docs: https://agnes-ai.com/doc/overview
- Platform: https://platform.agnes-ai.com/
- International API base URL (primary): `https://apihub.agnes-ai.com/v1`
- International API base URL (alternate): `https://apihub.agnes-ai.cn/v1`
- China API base URL: `https://api.agnes-ai.cn/v1`
