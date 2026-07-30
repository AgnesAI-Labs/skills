# Agnes AI Troubleshooting Reference

Use this file when an Agnes AI API request fails or behaves differently than expected.

## Checklist

1. Confirm the API key is loaded from `AGNES_API_KEY`.
2. Confirm the header is `Authorization: Bearer <key>`.
3. Confirm the base URL matches the selected service route.
4. Confirm the model name and endpoint match.
5. Remove secrets and reduce the request to a minimal reproducible example.
6. Check current RPM and quota limits.
7. Add retry with exponential backoff for transient errors.

## Base URL Cannot Connect

Use this decision flow only for network, DNS, TLS, or connection-timeout failures. Do not use endpoint switching as a workaround for request, authentication, permission, or quota errors.

1. Confirm the Base URL includes `/v1` exactly once.
2. Ask whether the user is using the International service or the China service.
3. For the International service, test `https://apihub.agnes-ai.com/v1` first. If it is unreachable, test `https://apihub.agnes-ai.cn/v1` with one minimal request and keep the reachable route.
4. For the China service, use `https://api.agnes-ai.cn/v1`.
5. Update the client's `AGNES_BASE_URL` or custom OpenAI-compatible provider setting, then retry the same minimal request.
6. If the result is `400`, `401`, `403`, `422`, or `429`, keep the selected route and troubleshoot the request, account, API key, permissions, or rate limit instead.

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
