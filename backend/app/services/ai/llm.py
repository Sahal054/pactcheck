"""Sync and async JSON adapters; OpenAI uses schema-enforced Structured Outputs."""

import json
import re
from typing import TypeVar
from pydantic import BaseModel
from openai import OpenAI, AsyncOpenAI
from app.config import settings

T = TypeVar("T", bound=BaseModel)


def _extract_json_dict(raw: str) -> dict:
    cleaned = re.sub(r"```(?:json)?\s*|```", "", raw.strip(), flags=re.IGNORECASE)
    decoder = json.JSONDecoder()
    for start in [0] + [m.start() for m in re.finditer(r"\{", cleaned)]:
        try:
            value, _ = decoder.raw_decode(cleaned[start:].lstrip())
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            continue
    raise ValueError("Model response did not contain a JSON object")


class LLMService:
    @staticmethod
    def _temperature(model: str) -> float:
        return 1.0 if "gpt-5" in model.lower() else 0.1

    def _configuration(self):
        provider = settings.llm_provider.lower()
        if provider == "openai":
            key, model = settings.openai_api_key, settings.openai_model
        elif provider == "openrouter":
            key, model = settings.openrouter_api_key, settings.openrouter_model
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        if not key:
            raise RuntimeError(
                f"Set {provider.upper()}_API_KEY in backend/.env or Settings"
            )
        kwargs = {"api_key": key, "timeout": 30, "max_retries": 1}
        if provider == "openrouter":
            kwargs["base_url"] = settings.openrouter_base_url
        return kwargs, model

    def _get_sync_client_and_model(self):
        kwargs, model = self._configuration()
        return OpenAI(**kwargs), model

    def _get_async_client_and_model(self):
        kwargs, model = self._configuration()
        return AsyncOpenAI(**kwargs), model

    @staticmethod
    def _parsed(response):
        message = response.choices[0].message
        if getattr(message, "refusal", None) or not message.parsed:
            raise ValueError("Model refused or returned no structured assessment")
        return message.parsed.model_dump()

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T] | None = None,
    ) -> dict:
        if settings.llm_provider == "mock":
            return {
                "connection": "ok",
                "mode": "mock",
                "message": "Deterministic mode; no remote request made.",
            }
        client, model = self._get_sync_client_and_model()
        kwargs = dict(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self._temperature(model),
        )
        try:
            if settings.llm_provider == "openai" and response_schema is not None:
                return self._parsed(
                    client.beta.chat.completions.parse(
                        **kwargs, response_format=response_schema
                    )
                )
            response = client.chat.completions.create(
                **kwargs, response_format={"type": "json_object"}
            )
            result = _extract_json_dict(response.choices[0].message.content or "")
            return (
                response_schema.model_validate(result).model_dump()
                if response_schema
                else result
            )
        finally:
            client.close()

    async def acomplete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[T] | None = None,
    ) -> dict:
        if settings.llm_provider == "mock":
            return {
                "connection": "ok",
                "mode": "mock",
                "message": "Deterministic mode; no remote request made.",
            }
        client, model = self._get_async_client_and_model()
        kwargs = dict(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self._temperature(model),
        )
        try:
            if settings.llm_provider == "openai" and response_schema is not None:
                return self._parsed(
                    await client.beta.chat.completions.parse(
                        **kwargs, response_format=response_schema
                    )
                )
            response = await client.chat.completions.create(
                **kwargs, response_format={"type": "json_object"}
            )
            result = _extract_json_dict(response.choices[0].message.content or "")
            return (
                response_schema.model_validate(result).model_dump()
                if response_schema
                else result
            )
        finally:
            await client.close()
