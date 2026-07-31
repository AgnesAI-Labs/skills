# Agnes AI Prompt Components

> **License:** Original work contributed under the
> [MIT License](https://opensource.org/licenses/MIT). This repository
> holds full rights to use, modify, sublicense, and redistribute this
> content with no further attribution or permission required.

Condensed vocabulary for assembling image and video prompts for
`agnes-image-2.1-flash` and `agnes-video-v2.0`. Pick one item per
category, combine with the formula, and append the matching negatives.

## Assembly Formula

| Medium | Order |
| --- | --- |
| Image | `[Subject] + [Style] + [Quality booster] + [Lighting] + [Composition] + [Details]` |
| Video | `[Subject action] + [Camera movement] + [Style] + [Lighting] + [Environment] + [Quality booster]` |

Always end with the negative block. Translate non-English input to
English for the final prompt — Agnes models respond better to English.

## Styles

| Style | Keywords | Best for |
| --- | --- | --- |
| Photorealistic | photorealistic, hyperrealistic, RAW photo, 8k uhd, DSLR | Portraits, products, landscapes |
| Cinematic | cinematic, film grain, anamorphic, color graded, 2.39:1 | Scenes, drama, video |
| Anime | anime style, cel-shaded, vibrant colors, Japanese animation | Characters, illustrations |
| 3D Render | 3D render, octane render, subsurface scattering, volumetric | Products, sci-fi, abstract |
| Watercolor | watercolor, soft edges, pastel palette, wet-on-wet | Prints, book covers |
| Oil Painting | oil painting, impasto, brush strokes visible, canvas texture | Fine art, portraits |
| Minimalist | minimalist, clean lines, negative space, flat design | Icons, posters, UI |
| Cyberpunk | neon-lit, cyberpunk, holographic, dark atmosphere, rain | Night scenes, sci-fi |
| Editorial | editorial photography, magazine quality, styled | Fashion, brand imagery |
| Concept Art | concept art, matte painting, environment design | Games, pre-visualization |

## Quality Boosters

Three layers. Stack top-down; skip the ones that do not match the medium.

| Tier | Keywords | When |
| --- | --- | --- |
| Universal | highly detailed, sharp focus, professional | Every prompt (default) |
| Photo-grade | 8k uhd, high dynamic range, natural lighting, crisp details | Photo or 3D realism |
| Video-grade | smooth motion, high frame rate, cinematic quality, broadcast-ready | All video prompts |

For photorealistic video, combine Universal + Photo-grade + Video-grade.
For stylized video, drop Photo-grade to avoid keyword bloat.

## Lighting

| Type | Keywords | Mood |
| --- | --- | --- |
| Golden hour | golden hour, warm sunlight, long shadows, amber glow | Warm, nostalgic |
| Blue hour | blue hour, twilight, cool ambient, dusk | Calm, urban |
| Studio soft | soft studio lighting, three-point, diffused, even | Clean, neutral |
| Dramatic | chiaroscuro, rim lighting, high contrast, single source | Moody, theatrical |
| Neon | neon glow, colored lighting, pink and blue | Futuristic, nightlife |
| Backlit | backlit, silhouette, lens flare, glowing edges | Ethereal, hopeful |
| Volumetric | volumetric lighting, god rays, light shafts, atmospheric | Epic, cinematic |
| Overcast | overcast sky, soft diffused daylight, no harsh shadows | Calm, documentary |

## Composition

| Type | Keywords |
| --- | --- |
| Close-up | close-up, macro, tight crop, shallow depth of field, bokeh |
| Wide / Establishing | wide-angle, panoramic, establishing shot, expansive |
| Aerial | aerial view, drone shot, bird's eye view, top-down |
| Low angle | low angle, looking up, heroic, imposing |
| Eye level | eye-level, straight-on, natural perspective |
| Dutch angle | dutch angle, tilted, diagonal, unsettling |
| Rule of thirds | rule of thirds, off-center subject, balanced negative space |
| Frame within frame | framed by doorway, window, archway, natural frame |

## Details & Environment

One or two short phrases that close out the prompt. For images, add
texture or depth cues; for video, add environmental motion. Examples:
`shallow depth of field`, `bokeh background`, `rain falling`, `crowd
motion`, `leaves rustling`, `slow motion`.

## Negative Prompts

Maximum 30 negative keywords per prompt. Universal + one subject
category + video (if video) + style conflict = typical set. Lowercase,
comma-separated, no other punctuation. Line breaks are for readability
only; combine into one comma-separated string before sending.

### Universal (every generation)

```
blurry, low quality, pixelated, watermark, signature, text overlay,
jpeg artifacts, cropped, out of frame
```

### Human / Anatomy (when people appear)

```
deformed fingers, extra digits, malformed hands, fused fingers,
missing fingers, extra limbs, bad anatomy, asymmetrical eyes,
mutated, deformed face, cross-eyed, poorly drawn hands, clone face
```

### Video-specific (every video)

```
flickering, frame inconsistency, jittery, sudden cuts,
morphing artifacts, temporal aliasing, warping, unstable edges,
ghosting, frame stuttering
```

### Style Conflicts

Add the conflicting block when a style is chosen.

#### When style = Photorealistic

```
cartoon, anime, illustration, painting, sketch, cel-shaded, flat color
```

#### When style = Anime / Illustration

```
photorealistic, photograph, 3D render, hyperrealistic, DSLR, RAW photo
```

#### When style = Cinematic

```
flat lighting, amateur, snapshot, overexposed, webcam quality
```

## Camera Movement (video)

| Movement | Keywords | Feel |
| --- | --- | --- |
| Push in | slow push-in, dolly forward, gradual zoom in | Intimacy, focus |
| Pull back | pull-back, dolly out, reveal shot, zoom out | Context, scale |
| Orbit | orbit shot, 360 rotation, arc around, circling | Hero moment, showcase |
| Tracking | tracking shot, follow cam, steadicam, lateral movement | Journey, energy |
| Crane up | crane up, rising shot, ascending, tilt up | Grandeur, hope |
| Static | static shot, locked camera, tripod, fixed frame | Calm, observation |
| Handheld | handheld, slight shake, documentary feel | Authenticity, urgency |
| Pan / Tilt | slow pan left, pan right, tilt up, tilt down | Survey, discovery |

## Auto-Rules

1. Translate any non-English input to English before sending to the model.
2. Cap negatives at 30 keywords; trim to the most relevant per subject.
3. Every image prompt picks exactly one style, one lighting, one composition.
4. Every video prompt specifies at least one camera movement (even static).
5. If the user request is vague, ask up to 3 focused questions: subject, style, use case.
6. Always return both the saved file path and the API URL to the user.
