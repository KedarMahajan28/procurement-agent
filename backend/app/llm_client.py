"""Thin wrapper around the Groq API so agents don't each hardcode client setup.

Set GROQ_API_KEY in the environment before running the backend.
"""
import json
import os

from groq import Groq

DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

_client = None


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Export it before starting the backend."
            )
        _client = Groq(api_key=api_key)
    return _client


def chat_json(system_prompt: str, user_prompt: str, model: str = DEFAULT_MODEL) -> dict:
    """Calls the LLM and parses a strict-JSON response. Used for extraction /
    structured-output style calls where deterministic downstream code needs
    reliable fields, not prose."""
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content
    return json.loads(content)


def chat_text(system_prompt: str, user_prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Calls the LLM for free-text output — used for explanations/reasoning,
    never for numbers that feed calculations."""
    client = get_client()
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()
