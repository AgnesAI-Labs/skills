# Agnes AI Agent Compatibility

Last updated: 2026-07-30 Asia/Singapore

This skill is packaged for Codex, but its instructions can also be used by other agent software that supports external Markdown instructions, custom providers, or OpenAI-compatible model endpoints.

## Compatibility Position

| Agent software | How to use this skill |
| --- | --- |
| Codex | Install `agnes-ai-models` as a Codex skill from this GitHub repository. |
| OpenClaw | Use `SKILL.md` and the reference files as model-provider instructions. Configure the OpenAI-compatible base URL, API key, and model name in the agent settings. |
| Hermes | Use this directory as external instructions or model-provider documentation. Configure the Agnes endpoint as an OpenAI-compatible provider if supported. |
| Manus | Import or reference the Markdown files as knowledge/instructions, then configure Agnes API access through a custom OpenAI-compatible provider if supported. |
| Custom agents | Use the model catalog and troubleshooting references to configure calls against the Agnes API gateway. |

## Provider Settings

Use these defaults unless the target agent requires different field names:

| Setting | Value |
| --- | --- |
| Provider type | OpenAI-compatible |
| Base URL | Choose the service route below. |
| API key | User-provided Agnes API key |
| API key environment variable | `AGNES_API_KEY` |
| Chat model | `agnes-2.5-flash` |
| Image model | `agnes-image-2.1-flash` |
| Video model | `agnes-video-v2.0` |

## Regional Endpoint Routing

| Service route | Base URL |
| --- | --- |
| International service (primary) | `https://apihub.agnes-ai.com/v1` |
| International service (alternate) | `https://apihub.agnes-ai.cn/v1` |
| China service | `https://api.agnes-ai.cn/v1` |

For the International service, start with the primary route and use the alternate route only when the primary route has a network, DNS, TLS, or connection-timeout failure. For the China service, use the China service route. Do not rotate routes after `400`, `401`, `403`, `422`, or `429` responses; troubleshoot the request, key, account, permissions, or limits for the selected service instead.

## Recommended Agent Instruction

Use this instruction when adding Agnes AI to another agent:

```text
Use Agnes AI through the OpenAI-compatible API gateway.
Base URL: Select the service-specific Base URL from the Regional Endpoint Routing table before making requests.
Read the Agnes AI skill documentation from:
https://github.com/AgnesAI-Labs/skills/tree/main/agnes-ai-models
Before making requests, confirm the user has registered on the matching Agnes service and has an API key for that service.
Never expose API keys, bearer tokens, private logs, screenshots containing secrets, or customer data.
For model choices, use agnes-2.5-flash for chat, agnes-image-2.1-flash for image generation and editing, and agnes-video-v2.0 for video generation.
```

## Notes

- Codex can install the skill directly. Other agents may not understand the Codex skill package format, but they can still use the Markdown instructions and OpenAI-compatible provider settings.
- Model availability, rate limits, context windows, and quota rules may change. Confirm production-critical values in the official docs or Agnes Platform console.
- For common errors and retry guidance, read `troubleshooting.md`.
