import json
import os
from abc import ABC, abstractmethod
from typing import Optional

import httpx
from pydantic import ValidationError

from .compiler import compile_intent
from .models import CompileResponse, DirectorProgram


SYSTEM_PROMPT = """You are the intent compiler for Football Director OS.
Convert the user's football monitoring request into one JSON object matching the supplied schema.
Never invent event fields. Only use PASS, SHOT, POSSESSION_RECOVERY, POSSESSION_LOSS,
TACKLE, PRESSURE, GOAL, or SUBSTITUTION. The only pitch regions are DEFENSIVE_THIRD,
MIDDLE_THIRD, and ATTACKING_THIRD. Supported operators are EVENT_MATCH,
COUNT_THRESHOLD, and ORDERED_SEQUENCE (exactly two filters). Return JSON only.
If the request needs continuous tracking, formations, inferred space, or video, return
{"status":"unsupported","message":"..."}. If it is ambiguous, return
{"status":"clarification_required","message":"..."}.
"""


class IntentProvider(ABC):
    name: str

    @abstractmethod
    async def compile(self, instruction: str) -> CompileResponse:
        raise NotImplementedError


class DeterministicProvider(IntentProvider):
    name = "deterministic-fallback"

    async def compile(self, instruction: str) -> CompileResponse:
        return compile_intent(instruction)


class FoundryProvider(IntentProvider):
    """OpenAI-compatible Microsoft Foundry adapter with strict local validation."""

    name = "microsoft-foundry"

    def __init__(self, endpoint: str, api_key: str, model: str):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def compile(self, instruction: str) -> CompileResponse:
        schema = DirectorProgram.model_json_schema()
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT + "\nSchema:\n" + json.dumps(schema)},
                {"role": "user", "content": instruction},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Content-Type": "application/json", "api-key": self.api_key, "Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        try:
            candidate = json.loads(content)
            if candidate.get("status") in {"unsupported", "clarification_required"}:
                return CompileResponse(
                    status=candidate["status"], original_instruction=instruction,
                    message=candidate.get("message"), provider=self.name,
                )
            program = DirectorProgram.model_validate(candidate.get("program", candidate))
        except (json.JSONDecodeError, ValidationError, TypeError, KeyError) as exc:
            return CompileResponse(
                status="clarification_required", original_instruction=instruction,
                message=f"Model output failed deterministic validation: {type(exc).__name__}", provider=self.name,
            )
        return CompileResponse(status="valid", original_instruction=instruction, program=program, provider=self.name)


def configured_provider() -> IntentProvider:
    endpoint = os.getenv("FOUNDRY_ENDPOINT")
    api_key = os.getenv("FOUNDRY_API_KEY")
    model = os.getenv("FOUNDRY_MODEL")
    if endpoint and api_key and model:
        return FoundryProvider(endpoint, api_key, model)
    return DeterministicProvider()
