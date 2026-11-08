"""Model wrapper — the only file that is provider-specific.

To switch providers, set LLM_PROVIDER in your .env file:
    LLM_PROVIDER=anthropic   (default) — uses ANTHROPIC_API_KEY
    LLM_PROVIDER=openai               — uses OPENAI_API_KEY
    LLM_PROVIDER=azure                — uses AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT

Everything outside this file uses the normalized LLMResponse interface
and never imports from anthropic or openai directly.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ── Provider and model selection ──────────────────────────────────────────────

PROVIDER: str = os.environ.get("LLM_PROVIDER", "anthropic").lower()

_ANTHROPIC_DEFAULT = "claude-haiku-5-5"   # swap to claude-sonnet-5-5 for published runs
_OPENAI_DEFAULT    = "gpt-4o-mini"        # swap to gpt-4o for published runs
_AZURE_DEFAULT     = "gpt-4.1-nano"       # must match your Azure deployment name

if PROVIDER == "openai":
    MODEL_ID: str = os.environ.get("OPENAI_MODEL", _OPENAI_DEFAULT)
elif PROVIDER == "azure":
    # Azure deployment name — must match the name you gave when deploying the model
    MODEL_ID = os.environ.get("AZURE_OPENAI_DEPLOYMENT", _AZURE_DEFAULT)
else:
    MODEL_ID = os.environ.get("ANTHROPIC_MODEL", _ANTHROPIC_DEFAULT)

TEMPERATURE: float = 0.0  # fixed for reproducibility — record in RUNS.md


# ── Normalized response types ─────────────────────────────────────────────────
# agent.py uses only these types, never Anthropic or OpenAI SDK objects.

@dataclass
class TextBlock:
    text: str
    type: str = "text"


@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]
    type: str = "tool_use"


@dataclass
class LLMResponse:
    """Provider-neutral response returned by chat().

    stop_reason is "end_turn" for a final text reply,
    or "tool_use" when the model wants to call a tool.
    content is a list of TextBlock and/or ToolUseBlock objects.
    """
    stop_reason: str
    content: list[TextBlock | ToolUseBlock] = field(default_factory=list)


# ── Lazy client init ──────────────────────────────────────────────────────────

_anthropic_client = None
_openai_client    = None


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. "
                "Copy .env.example to .env and add your key."
            )
        _anthropic_client = anthropic.Anthropic(api_key=key)
    return _anthropic_client


def _get_openai():
    global _openai_client
    if _openai_client is None:
        import openai
        if PROVIDER == "azure":
            endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
            key = os.environ.get("AZURE_OPENAI_API_KEY")
            if not endpoint:
                raise EnvironmentError(
                    "AZURE_OPENAI_ENDPOINT is not set. "
                    "Example: https://<resource>.openai.azure.com/openai/v1"
                )
            if not key:
                raise EnvironmentError(
                    "AZURE_OPENAI_API_KEY is not set. "
                    "Copy .env.example to .env and add your Azure key."
                )
            _openai_client = openai.OpenAI(base_url=endpoint, api_key=key)
        else:
            key = os.environ.get("OPENAI_API_KEY")
            if not key:
                raise EnvironmentError(
                    "OPENAI_API_KEY is not set. "
                    "Copy .env.example to .env and add your key."
                )
            _openai_client = openai.OpenAI(api_key=key)
    return _openai_client


# ── Provider adapters ─────────────────────────────────────────────────────────

def _chat_anthropic(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None,
    system: str | None,
) -> LLMResponse:
    kwargs: dict[str, Any] = {
        "model": MODEL_ID,
        "max_tokens": 1024,
        "temperature": TEMPERATURE,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system
    if tools:
        kwargs["tools"] = tools

    raw = _get_anthropic().messages.create(**kwargs)

    content: list[TextBlock | ToolUseBlock] = []
    for block in raw.content:
        if block.type == "text":
            content.append(TextBlock(text=block.text))
        elif block.type == "tool_use":
            content.append(ToolUseBlock(id=block.id, name=block.name, input=block.input))

    stop = "tool_use" if raw.stop_reason == "tool_use" else "end_turn"
    return LLMResponse(stop_reason=stop, content=content)


def _anthropic_tools_to_openai(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert Anthropic tool schema format to OpenAI function-calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("input_schema", {}),
            },
        }
        for t in tools
    ]


def _chat_openai(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None,
    system: str | None,
) -> LLMResponse:
    # OpenAI puts the system prompt as the first message
    oai_messages: list[dict[str, Any]] = []
    if system:
        oai_messages.append({"role": "system", "content": system})

    # Convert Anthropic-format messages to OpenAI format
    for msg in messages:
        role = msg["role"]
        body = msg["content"]

        if isinstance(body, str):
            oai_messages.append({"role": role, "content": body})
            continue

        if isinstance(body, list):
            # Tool results from agent.py
            if role == "user" and all(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in body
            ):
                for b in body:
                    oai_messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": b["tool_use_id"],
                            "content": b["content"],
                        }
                    )
                continue

            # Assistant message with tool_use blocks (TextBlock / ToolUseBlock objects)
            if role == "assistant":
                text_parts = []
                tool_calls = []
                for block in body:
                    if isinstance(block, TextBlock):
                        text_parts.append(block.text)
                    elif isinstance(block, ToolUseBlock):
                        tool_calls.append(
                            {
                                "id": block.id,
                                "type": "function",
                                "function": {
                                    "name": block.name,
                                    "arguments": json.dumps(block.input),
                                },
                            }
                        )
                oai_msg: dict[str, Any] = {"role": "assistant"}
                if text_parts:
                    oai_msg["content"] = " ".join(text_parts)
                if tool_calls:
                    oai_msg["tool_calls"] = tool_calls
                oai_messages.append(oai_msg)
                continue

        oai_messages.append({"role": role, "content": str(body)})

    kwargs: dict[str, Any] = {
        "model": MODEL_ID,
        "temperature": TEMPERATURE,
        "messages": oai_messages,
    }
    if tools:
        kwargs["tools"] = _anthropic_tools_to_openai(tools)
        kwargs["tool_choice"] = "auto"

    raw = _get_openai().chat.completions.create(**kwargs)
    choice = raw.choices[0]
    msg = choice.message

    content: list[TextBlock | ToolUseBlock] = []
    if msg.content:
        content.append(TextBlock(text=msg.content))
    if msg.tool_calls:
        for tc in msg.tool_calls:
            content.append(
                ToolUseBlock(
                    id=tc.id,
                    name=tc.function.name,
                    input=json.loads(tc.function.arguments),
                )
            )

    stop = "tool_use" if choice.finish_reason == "tool_calls" else "end_turn"
    return LLMResponse(stop_reason=stop, content=content)


# ── Public interface ──────────────────────────────────────────────────────────

def chat(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    system: str | None = None,
) -> LLMResponse:
    """Send a message sequence to the configured provider.

    Returns a normalized LLMResponse — provider-agnostic.
    Set LLM_PROVIDER in .env to switch between anthropic and openai.
    """
    if PROVIDER in ("openai", "azure"):
        return _chat_openai(messages, tools, system)
    return _chat_anthropic(messages, tools, system)
