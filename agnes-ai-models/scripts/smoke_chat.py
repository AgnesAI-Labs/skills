#!/usr/bin/env python3
"""Smoke test for Agnes AI chat completions.

Set AGNES_API_KEY before running:

    export AGNES_API_KEY="your_api_key_here"
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

    client = OpenAI(
        api_key=api_key,
        base_url="https://apihub.agnes-ai.com/v1",
    )

    response = client.chat.completions.create(
        model="agnes-2.0-flash",
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
