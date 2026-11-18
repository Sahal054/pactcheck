import json
from openai import OpenAI
from app.config import settings

class LLMService:
    def complete_json(self, system_prompt: str, user_prompt: str) -> dict:
        provider = settings.llm_provider.lower()
        if provider == "mock":
            return {"mock": True, "message": "Mock mode: configure OpenRouter or OpenAI for live AI analysis."}
        if provider == "openrouter":
            if not settings.openrouter_api_key:
                raise RuntimeError("Set OPENROUTER_API_KEY in backend/.env")
            client = OpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url)
            model = settings.openrouter_model
        elif provider == "openai":
            if not settings.openai_api_key:
                raise RuntimeError("Set OPENAI_API_KEY in backend/.env")
            client = OpenAI(api_key=settings.openai_api_key)
            model = settings.openai_model
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
