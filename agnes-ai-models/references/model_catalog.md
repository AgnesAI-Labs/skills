# Agnes AI Model Reference

Last updated: 2026-06-28 00:00 Asia/Singapore

These values are public reference values. Model availability, rate limits, pricing, context windows, and quota rules may change. Confirm production-critical values in the official docs or Agnes Platform console.

## Base URLs

| Use case | Base URL |
| --- | --- |
| OpenAI-compatible API | `https://apihub.agnes-ai.com/v1` |
| Video result polling | `https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>` |

## Models

| Model | Type | Endpoint | Use cases |
| --- | --- | --- | --- |
| `agnes-2.0-flash` | Text and vision-language | `/v1/chat/completions` | Chat, coding, reasoning, tools, streaming, image understanding, agent workflows |
| `agnes-image-2.0-flash` | Image generation and editing | `/v1/images/generations` | Fast image generation, text-to-image, image-to-image |
| `agnes-image-2.1-flash` | Image generation and editing | `/v1/images/generations` | Higher quality image generation and editing |
| `agnes-video-v2.0` | Video generation | `/v1/videos` | Text-to-video, image-to-video, multi-image video, keyframe animation |

## Reference Limits

| Model type | User type | Public request RPM | Actual executable RPM |
| --- | --- | ---: | ---: |
| Text models | Free / default | 30 | 20 |
| Text models | Enterprise | 60 | 40 |
| Text models | Token Plan | 1,000 | 1,000 |
| Video models | Free / default | 2 | 1 |
| Video models | Enterprise | 2 | 2 |
| Video models | Token Plan | 6 | 5 |

Image model RPM is resolution-specific:

| User type | 1K actual RPM | 2K actual RPM | 3K actual RPM | 4K actual RPM |
| --- | ---: | ---: | ---: | ---: |
| Free / default | 20 | 10 | 1 | 1 |
| Enterprise | 40 | 20 | 1 | 1 |
| Token Plan | 100 | 80 | 1 | 1 |

## Token Plan Quotas

| Plan | `agnes-2.0-flash` | `agnes-image-2.0/2.1-flash` | `agnes-video-v2.0` |
| --- | --- | --- | --- |
| Starter | 1,500 requests per 5 hours; 15,000 requests per week | 4,000 images per day | 500 seconds per day |
| Plus | 7,500 requests per 5 hours; 75,000 requests per week | 4,000 images per day | 500 seconds per day |
| Pro | 30,000 requests per 5 hours; 300,000 requests per week | 4,000 images per day | 500 seconds per day |

Token Plan users are subject to both RPM limits and subscription quotas.
