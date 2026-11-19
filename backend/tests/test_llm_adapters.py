import asyncio
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock
import pytest
from app.config import settings
from app.schemas.models import LLMClauseEvaluation
from app.services.ai.llm import LLMService


def response(parsed=None, content=None, refusal=None):
    return NS(choices=[NS(message=NS(parsed=parsed, content=content, refusal=refusal))])


@pytest.mark.parametrize("asynchronous", [False, True])
def test_openai_uses_structured_outputs(asynchronous, monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    evaluation = LLMClauseEvaluation(
        risk_level="Low",
        compliance_status="Compliant",
        explanation="Aligned with policy.",
    )
    parse = (
        AsyncMock(return_value=response(parsed=evaluation))
        if asynchronous
        else Mock(return_value=response(parsed=evaluation))
    )
    close = AsyncMock() if asynchronous else Mock()
    client = NS(
        beta=NS(chat=NS(completions=NS(parse=parse))),
        chat=NS(completions=NS(create=Mock())),
        close=close,
    )
    llm = LLMService()
    monkeypatch.setattr(
        llm,
        "_get_async_client_and_model" if asynchronous else "_get_sync_client_and_model",
        lambda: (client, "gpt-4o-mini"),
    )
    output = (
        asyncio.run(llm.acomplete_json("system", "user", LLMClauseEvaluation))
        if asynchronous
        else llm.complete_json("system", "user", LLMClauseEvaluation)
    )
    assert output["compliance_status"] == "Compliant"
    assert parse.call_args.kwargs["response_format"] is LLMClauseEvaluation
    assert parse.call_args.kwargs["messages"][0]["role"] == "system"
    client.chat.completions.create.assert_not_called()
    close.assert_called_once()


@pytest.mark.parametrize("asynchronous", [False, True])
def test_openrouter_fenced_json_and_client_cleanup(asynchronous, monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openrouter")
    create = (
        AsyncMock(return_value=response(content='```json\n{"connection":"ok"}\n```'))
        if asynchronous
        else Mock(return_value=response(content='```json\n{"connection":"ok"}\n```'))
    )
    close = AsyncMock() if asynchronous else Mock()
    client = NS(chat=NS(completions=NS(create=create)), close=close)
    llm = LLMService()
    monkeypatch.setattr(
        llm,
        "_get_async_client_and_model" if asynchronous else "_get_sync_client_and_model",
        lambda: (client, "free-model"),
    )
    output = (
        asyncio.run(llm.acomplete_json("system", "user"))
        if asynchronous
        else llm.complete_json("system", "user")
    )
    assert output == {"connection": "ok"}
    close.assert_called_once()


def test_structured_refusal_is_not_silently_downgraded(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "openai")
    client = NS(
        beta=NS(
            chat=NS(
                completions=NS(parse=Mock(return_value=response(refusal="declined")))
            )
        ),
        close=Mock(),
    )
    llm = LLMService()
    monkeypatch.setattr(llm, "_get_sync_client_and_model", lambda: (client, "model"))
    with pytest.raises(ValueError, match="refused"):
        llm.complete_json("system", "user", LLMClauseEvaluation)
    client.close.assert_called_once()
