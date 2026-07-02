# Agnes AI Troubleshooting Reference

Use this file when an Agnes AI API request fails or behaves differently than expected.

## Checklist

1. Confirm the API key is loaded from `AGNES_API_KEY`.
2. Confirm the header is `Authorization: Bearer <key>`.
3. Confirm the base URL is `https://apihub.agnes-ai.com/v1`.
4. Confirm the model name and endpoint match.
5. Remove secrets and reduce the request to a minimal reproducible example.
6. Check current RPM and quota limits.
7. Add retry with exponential backoff for transient errors.

## Common Status Codes

| Status | Meaning | Checks |
| --- | --- | --- |
| `400` | Invalid request | Required fields, JSON shape, parameter names, image URL accessibility, response format placement |
| `401` | Authentication failed | API key value, bearer format, account status, environment variable loading |
| `404` | Not found | Base URL, endpoint path, model name, `video_id`, resource existence |
| `408` | Timeout | Request size, network stability, retry behavior |
| `422` | Request could not be processed | Image edit payload, media URL accessibility, file type, dimensions |
| `429` | Rate limit exceeded | Plan, RPM, concurrency, polling frequency |
| `500` | Server error | Retry with backoff, simplify payload, test minimal request |
| `502` | Gateway/upstream error | Retry with backoff, check whether it is transient |
| `503` | Busy or unavailable | Retry later, reduce concurrency, avoid tight polling |
| `520` | Unknown upstream error | Retry with backoff, capture metadata for support |
| `522` | Connection timed out | Retry with backoff, reduce payload size |
| `524` | Gateway timeout | Retry with backoff, avoid long synchronous waits |

## Video Polling

Current video workflows should poll with `video_id`:

```text
GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>
```

Do not use `task_id` for current result polling unless a legacy workflow explicitly documents it.
