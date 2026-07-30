#!/usr/bin/env python3
"""Smoke test for Agnes AI chat completions.

Set AGNES_API_KEY before running:

    export AGNES_API_KEY="your_api_key_here"

Optionally select a regional route:

    export AGNES_BASE_URL="https://apihub.agnes-ai.com/v1"

Then run:

    python scripts/smoke_chat.py
"""

import os
import sys

from openai import OpenAI


def main() -> int:
    api_key = os.environ.get("AGNES_API_KEY")
    if not api_key:
        print("AGNES_API_KEY is not set.", file=sys.stderr)
        return 2

    base_url = os.environ.get(
        "AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1"
    ).rstrip("/")
    print(f"Using AGNES_BASE_URL={base_url}", file=sys.stderr)

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    response = client.chat.completions.create(
        model="agnes-2.5-flash",
        messages=[
            {
                "role": "user",
                "content": "Reply with one short sentence confirming the Agnes AI API works.",
            }
        ],
    )
    print(response.choices[0].message.content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
