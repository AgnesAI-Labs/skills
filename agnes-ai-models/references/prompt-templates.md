# Agnes AI Prompt Templates

> **License:** Original work contributed under the
> [MIT License](https://opensource.org/licenses/MIT). This repository
> holds full rights to use, modify, sublicense, and redistribute this
> content with no further attribution or permission required.

Prompt templates and structured-output guidance for the four runnable
helpers in `scripts/`: `image_understand.py`, `image_generate.py`,
`video_understand.py`, and `video_generate.py`. Pair with
`references/model_catalog.md` (models, limits) and
`references/troubleshooting.md` (errors, routing).

All endpoints are OpenAI-compatible and share the same base URL and
auth header (`Authorization: Bearer $AGNES_API_KEY`).

## 1. Image Understanding

| | |
|---|---|
| Model | `agnes-2.5-flash` (text and vision-language) |
| Endpoint | `POST /v1/chat/completions` |
| Helper | `scripts/image_understand.py` |

### System prompt

No system prompt is required; the instruction travels in the user
message next to the image. Optional system prompt when you need a
stable analyst persona:

```text
You are a precise visual analysis assistant. Describe only what is
visible or clearly inferable. Do not invent details.
```

### User prompt templates

The image is sent as an `image_url` content part (a public URL or a
`data:` URL for local files). Three output formats:

**text** — free-form answer:

```text
{your instruction}
```

**structured** (default in the helper) — markdown sections:

```text
{your instruction}

Provide a structured analysis with the following sections:
- Summary (one sentence)
- Description (detailed)
- Subjects
- Style
- Color palette
- Composition
- Mood
- Text in image (if any)
- Metadata (dimensions, aspect ratio, format)
```

**json** — machine-readable:

```text
{your instruction}

Return the result as valid JSON matching this schema:
{schema below}
```

Append local file metadata when known, e.g.
`Image metadata: width=1920, height=1080, aspect_ratio=1920:1080.`

### Structured output schema (image)

```json
{
  "summary": "string",
  "description": "string",
  "subjects": ["string"],
  "style": "string",
  "color_palette": ["string"],
  "composition": "string",
  "mood": "string",
  "text_in_image": "string",
  "metadata": {
    "width": 0,
    "height": 0,
    "aspect_ratio": "string",
    "format": "string"
  }
}
```

### Parameters

| Parameter | Guidance |
|---|---|
| `temperature` | 0.2–0.5 for factual analysis; raise toward 0.7 for creative descriptions. |
| `max_tokens` | 2048 is enough for the full structured/JSON output. |

## 2. Image Generation

| | |
|---|---|
| Model | `agnes-image-2.1-flash` (generation and editing) |
| Endpoint | `POST /v1/images/generations` |
| Helper | `scripts/image_generate.py` |

### User prompt templates

Fill the bracketed placeholders, or use them as starting points.

**Creative design / concept art**

```text
A [style] concept art of [subject], [environment], [lighting], [mood].
Highly detailed, atmospheric, cinematic composition.
```

Example:

```text
A cyberpunk concept art of a neon-lit street market in Tokyo, rainy night,
reflections on wet pavement, moody blue and magenta lighting, cinematic composition.
```

**Marketing / product visual**

```text
A clean product photo of [product] on [surface/background], [lighting],
[angle], minimal shadows, professional commercial photography style.
```

Example:

```text
A clean product photo of a matte black wireless headphone on a marble surface,
soft studio lighting, 3/4 angle, professional commercial photography style.
```

**Social media creative**

```text
A bold, eye-catching [platform] post image featuring [subject], [colors],
[text/mood], flat design or 3D render style, high contrast.
```

Example:

```text
A bold Instagram post image featuring a rocket launch, deep purple and orange gradient,
energetic and inspiring mood, 3D render style, high contrast.
```

**High-density visual scene**

```text
A richly detailed scene of [setting], filled with [elements], [time of day],
[art style], deep layers, intricate textures.
```

Example:

```text
A richly detailed scene of a fantasy library inside a giant tree, filled with glowing books,
floating candles and spiral staircases, golden hour light, painterly digital art style,
deep layers, intricate textures.
```

**Image transformation / style transfer** (image-to-image, pass a
reference image)

```text
Transform this image into [target style], keeping the original composition and subject.
[lighting change], [color grading], [mood shift].
```

Example:

```text
Transform this image into a hand-drawn watercolor illustration,
keeping the original composition and subject. Soft natural lighting,
pastel color grading, calm and nostalgic mood.
```

**Thumbnail / banner / app asset**

```text
A [dimensions]-friendly [asset type] showing [subject], clear focal point,
bold colors, readable negative space, [style].
```

Example:

```text
A YouTube thumbnail-friendly image showing a surprised programmer looking at a screen,
clear focal point, bold orange and dark blue colors, readable negative space,
3D cartoon style.
```

**Negative prompts / constraints** — append when needed:

- `no text, no watermark, no signature`
- `minimalist, clean background`
- `photorealistic, 8k, highly detailed`
- `anime style, cel-shaded, vibrant colors`

### Size presets

| Use case | Recommended size | Aspect ratio |
|---|---|---|
| Social media post (square) | `1024x1024` | 1:1 |
| Social media story / vertical | `768x1344` | 9:16 |
| Banner / cover | `1792x1024` | 16:9 |
| Wallpaper / landscape | `1344x768` | 16:9 |
| Product shot | `1024x1024` or `1152x768` | 1:1 or 3:2 |
| Poster / portrait | `1024x1344` | 3:4 |

### Parameters

| Parameter | Guidance |
|---|---|
| `size` | `WIDTHxHEIGHT` string. Higher resolutions consume more quota: per `model_catalog.md`, free-tier actual RPM drops from ~20 at 1K to 1 at 3K/4K. |
| `n` | Images per request (default 1). |
| `image` | Image-to-image reference(s), sent as an array of URLs or `data:` URLs. |

**Response handling note:** items may carry `url` or `b64_json`; read
whichever is present. The service has been observed returning a URL
even when base64 output was requested, so handle both defensively.
`revised_prompt`, when present, echoes any prompt rewriting.

## 3. Video Understanding

| | |
|---|---|
| Model | `agnes-2.5-flash` (frames analyzed as images) |
| Endpoint | `POST /v1/chat/completions` |
| Helper | `scripts/video_understand.py` (requires ffmpeg) |

The chat endpoint consumes images, not raw video. The helper samples
`N` evenly spaced frames with ffmpeg (scaled down, e.g. width 512, to
save tokens) and sends them as `image_url` parts alongside the
instruction, e.g. `Extracted keyframes at: 00:00:04.000, 00:00:08.000, ...`.

### User prompt templates

Same three output formats as image understanding; the structured and
JSON variants reference keyframes:

**structured** (default in the helper):

```text
{your instruction}

Extracted keyframes at: {comma-separated timestamps}

Provide a structured analysis with the following sections:
- Summary (one sentence)
- Keyframes analyzed (describe what happens at each extracted timestamp)
- Scene-by-scene description
- Settings
- Characters / actions
- Camera movement
- Visual style
- Mood / tone
- Audio description (if inferable)
- Metadata (duration, resolution, frame rate, format)
```

Append local file metadata when known, e.g.
`Video metadata: duration=30.0s, resolution=1920x1080, frame_rate=30/1.`

### Structured output schema (video)

```json
{
  "summary": "string",
  "keyframes": [
    {"timestamp": "00:00:28.000", "description": "string"}
  ],
  "scenes": [
    {"start": "00:00", "end": "00:05", "description": "string"}
  ],
  "settings": ["string"],
  "characters_actions": ["string"],
  "camera_movement": "string",
  "visual_style": "string",
  "mood": "string",
  "audio_description": "string",
  "metadata": {
    "duration_seconds": 0,
    "resolution": "string",
    "frame_rate": 0,
    "format": "string"
  }
}
```

### Parameters

| Parameter | Guidance |
|---|---|
| Frames sampled | 5 is a good default; increase for long or fast-cutting videos (each frame costs tokens). |
| Frame width | Downscale to ~512px width for analysis; detail-heavy tasks (OCR) may need more. |
| `temperature` | 0.2–0.5 for factual description. |
| `max_tokens` | 2048 covers the structured/JSON output for most videos. |

## 4. Video Generation

| | |
|---|---|
| Model | `agnes-video-v2.0` (text-to-video, image-to-video) |
| Create | `POST /v1/videos` |
| Poll | `GET {service root}/agnesapi?video_id=<VIDEO_ID>` (service root = base URL without `/v1`) |
| Helper | `scripts/video_generate.py` |

### User prompt templates

**Text-to-video cinematic**

```text
A cinematic [shot type] of [scene], [time of day], [lighting], [camera movement],
[subject action], atmospheric, high quality.
```

Example:

```text
A cinematic wide shot of a futuristic city at night with neon lights and flying cars,
slow camera pan across the skyline, atmospheric fog, high quality.
```

**Image-to-video animation** (pass a first-frame image)

```text
Animate this scene: [subject] [action], [camera movement], [mood], smooth motion,
keep visual style consistent.
```

Example:

```text
Animate this scene: cherry blossoms falling gently in a Japanese garden,
slow camera drift forward, peaceful spring mood, smooth motion,
keep the painterly Ghibli-style visual consistent.
```

**Product demo motion**

```text
A smooth product showcase of [product], [rotation or movement], clean studio background,
professional lighting, subtle reflections, 4k commercial look.
```

Example:

```text
A smooth product showcase of a sleek smartwatch, slow 360-degree rotation,
clean gradient background, professional lighting, subtle reflections,
4k commercial look.
```

**Social media short**

```text
A fast-paced, eye-catching short clip for [platform], featuring [subject],
[colors/style], [camera movement], energetic mood, loop-friendly.
```

Example:

```text
A fast-paced, eye-catching short clip for TikTok, featuring abstract 3D shapes morphing,
bold purple and orange gradient style, dynamic camera zooms, energetic mood, loop-friendly.
```

**Keyframe / transition animation** (multiple keyframe images; advanced
payload, edit manually)

```text
Generate a smooth cinematic transition between the keyframes, maintaining visual
consistency and natural camera movement.
```

**Character / portrait animation** (pass a portrait image)

```text
Bring this portrait to life with subtle [expression/motion], gentle camera movement,
keep the subject's likeness and style consistent.
```

Example:

```text
Bring this portrait to life with subtle breathing and a gentle smile,
slight camera push-in, keep the subject's likeness and digital painting style consistent.
```

### Parameters

| Parameter | Guidance |
|---|---|
| `width`, `height` | Defaults 1152x768. For image-to-video, match the source image resolution. |
| `frame_rate` | Default 24. |
| `num_frames` | Must be `8n+1` and `<= 441`. The helper derives it from `duration * frame_rate` and snaps down to the grid (e.g. 5s at 24fps → 120 → 113 frames); snapping down favors generation speed and reliability over exact duration. |
| `image` | Starting-frame URL or `data:` URL for image-to-video. |

### Polling and rate limits

- Creation returns `video_id` (and usually `task_id`). Poll with
  `video_id`; do not use `task_id` for current result polling unless a
  legacy workflow explicitly documents it.
- Terminal statuses: `completed`, `failed`, `cancelled`. A `progress`
  percentage is typically included while running.
- Poll every 10s or slower. Video rate limits are tight (see
  `model_catalog.md`: free tier ~1–2 requests/min); aggressive polling
  triggers `429`.
- On `completed`, the result URL may appear in `url`, `video_url`, or
  `remixed_from_video_id` depending on workflow; check them in that
  order.
- Keep durations short (3–5s) for faster generation and a lower
  failure rate. English prompts tend to be more stable than Chinese
  prompts. Mention camera movement (`slow pan`, `static shot`,
  `drone fly-over`) for stronger motion.
