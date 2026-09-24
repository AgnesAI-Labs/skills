# Agnes AI Model Reference

Last updated: 2026-09-24 00:00 Asia/Shanghai

These values are public reference values. Model availability, rate limits, pricing, context windows, and quota rules may change. Confirm production-critical values in the official docs or Agnes Platform console.

## Base URLs

| Use case | Base URL |
| --- | --- |
| OpenAI-compatible API | `https://apihub.agnes-ai.com/v1` |
| Video result polling | `https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>&model_name=<MODEL_ID>` |

## Models

| Model | Type | Endpoint | Use cases |
| --- | --- | --- | --- |
| `agnes-2.0-flash` | Text and vision-language | `/v1/chat/completions` | Chat, coding, reasoning, tools, streaming, image understanding, agent workflows |
| `agnes-image-2.5-flash` | Image generation and editing | `/v1/images/generations` | Text-to-image, image-to-image, multi-image composition, 1K–4K output |
| `agnes-video-2.5` | Video generation | `/v1/videos` | Text-to-video, keyframes, image/audio/video references, 720P–2K output |
| `agnes-video-2.5-flash` | Video generation | `/v1/videos` | Fast 720P text-to-video, keyframes, image/audio references |

The older `agnes-image-2.0-flash`, `agnes-image-2.1-flash`, and `agnes-video-v2.0` identifiers are legacy compatibility choices. Use the models above for new integrations.

## Image 2.5 Flash

- Model: `agnes-image-2.5-flash`
- Docs: `https://agnes-ai.com/en/docs/agnes-image-25-flash`
- Required request fields: `model`, `prompt`, `size`
- `size`: `1K`, `2K`, `3K`, or `4K`; combine with `ratio` (`1:1`, `3:4`, `4:3`, `16:9`, `9:16`, `2:3`, `3:2`, or `21:9`)
- Image editing/composition: provide `extra_body.image` as an array of public URLs or Data URI Base64 values
- Response format: `extra_body.response_format` accepts `url` or `b64_json`
- Response values are in `data[0].url` or `data[0].b64_json`
- Current official docs list supported output-resolution tiers and reference images as free; verify before production billing decisions

## Video 2.5

| Model | `size` | Reference media | Published rate |
| --- | --- | --- | --- |
| `agnes-video-2.5` | `720P`, `1080P`, `1K`, `2K` | Up to 8 images, 1 video, 3 audios; total media files ≤12 | 720P $0.025/sec; 1080P/1K $0.040/sec; 2K $0.055/sec |
| `agnes-video-2.5-flash` | `720P` only | Up to 5 images and 3 audios; reference videos are not supported | Docs currently show a limited-time $0/sec promotion; this may change |

Both models use `seconds` as a string from `"4"` to `"12"`, `n=1`, and modes `text`, `keyframe`, or `reference`. Use `first_frame`/`last_frame` for keyframes. Reference video input for the base model is supplied as `videos[].url`; do not use legacy `video_url`, `video_path`, or `video_reference` fields.

Poll every request with:

```text
GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>&model_name=<MODEL_ID>
```

Stop when the top-level `status` is `completed` or `failed`, then read the completed file from the top-level `url`. The create response may include `id`, `task_id`, and `video_id`; use `video_id` for retrieval.

## Limits and billing notes

Limits, promotions, RPM, quotas, and billing can change independently of the model API. Always confirm production-critical values in the linked official model page or Agnes Platform console. For Video 2.5, the documented billing formula is output seconds × output rate + input video seconds × input-video rate + excess reference-image count × image rate; the first five reference images are free.
