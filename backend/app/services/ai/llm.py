import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel
from openai import OpenAI, AsyncOpenAI
from app.config import settings

T = TypeVar("T", bound=BaseModel)


def _extract_json_dict(raw: str) -> dict:
    if not raw:
        return {}
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if m:
            return json.loads(m.group(0))
        raise


class LLMService:
    def _get_sync_client_and_model(self):
        provider = settings.llm_provider.lower()
        if provider == "openrouter":
            if not settings.openrouter_api_key:
                raise RuntimeError("Set OPENROUTER_API_KEY in backend/.env or Settings")
            return OpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url), settings.openrouter_model
        if provider == "openai":
            if not settings.openai_api_key:
                raise RuntimeError("Set OPENAI_API_KEY in backend/.env or Settings")
            return OpenAI(api_key=settings.openai_api_key), settings.openai_model
        raise ValueError(f"Unsupported LLM provider: {provider}")

    def _get_async_client_and_model(self):
        provider = settings.llm_provider.lower()
        if provider == "openrouter":
            if not settings.openrouter_api_key:
                raise RuntimeError("Set OPENROUTER_API_KEY in backend/.env or Settings")
            return AsyncOpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url), settings.openrouter_model
        if provider == "openai":
            if not settings.openai_api_key:
                raise RuntimeError("Set OPENAI_API_KEY in backend/.env or Settings")
            return AsyncOpenAI(api_key=settings.openai_api_key), settings.openai_model
        raise ValueError(f"Unsupported LLM provider: {provider}")

    def complete_json(self, system_prompt: str, user_prompt: str, response_schema: Type[T] | None = None) -> dict:
        provider = settings.llm_provider.lower()
        if provider == "mock":
            return {"mock": True, "message": "Mock mode active."}
        client, model = self._get_sync_client_and_model()

        if provider == "openai" and response_schema is not None:
            try:
                parsed_resp = client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                    response_format=response_schema,
                )
                msg = parsed_resp.choices[0].message
                if msg.parsed:
                    return msg.parsed.model_dump()
            except Exception:
                pass

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return _extract_json_dict(response.choices[0].message.content or "{}")

    async def acomplete_json(self, system_prompt: str, user_prompt: str, response_schema: Type[T] | None = None) -> dict:
        provider = settings.llm_provider.lower()
        if provider == "mock":
            return {"mock": True, "message": "Mock mode active."}
        client, model = self._get_async_client_and_model()

        if provider == "openai" and response_schema is not None:
            try:
                parsed_resp = await client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                    response_format=response_schema,
                )
                msg = parsed_resp.choices[0].message
                if msg.parsed:
                    return msg.parsed.model_dump()
            except Exception:
                pass

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return _extract_json_dict(response.choices[0].message.content or "{}")