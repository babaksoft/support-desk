"""Exercise the real SDK loop using synthetic provider responses."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from agents import ModelBehaviorError, UserError
from openai import AsyncOpenAI
from openai.types.responses import Response

from support_desk.domain import AnswerDraft, SourceId
from support_desk.infrastructure import AgentsAnswerGenerator
from support_desk.infrastructure.agent import MAX_OUTPUT_TOKENS


@pytest.mark.parametrize("scenario", ["answered", "insufficient", "unread_source"])
@pytest.mark.asyncio
async def test_sdk_executes_tool_and_validates_draft(
    draft: AnswerDraft, scenario: str
) -> None:
    """Follow a real SDK function call into the lookup and structured output.

    Args:
        draft:
            Valid authored draft fixture.
        scenario:
            Answer, evidence gap, or unread citation to exercise.
    """

    calls = _response(
        [
            {
                "type": "function_call",
                "id": "fc_1",
                "call_id": "call_1",
                "name": "lookup_references",
                "arguments": '{"source_ids":["BL-PLANS"]}',
                "status": "completed",
            }
        ]
    )
    if scenario == "insufficient":
        draft = AnswerDraft(
            status="insufficient_evidence",
            answer="Refund rules are unspecified; ask an operator.",
            evidence=(),
            review_status="unreviewed",
        )
    elif scenario == "unread_source":
        draft = AnswerDraft.model_validate(
            {
                **draft.model_dump(),
                "evidence": [{"source_id": "BL-ACCESS", "version": "1"}],
            }
        )
    final = _final(draft)

    async with AsyncOpenAI(api_key="synthetic", max_retries=0) as client:
        mocked = AsyncMock(side_effect=[calls, final])
        with patch.object(client.responses, "create", mocked):
            generator = AgentsAnswerGenerator(client, "synthetic-model")
            if scenario == "unread_source":
                with pytest.raises(ValueError, match="lookup tool"):
                    await generator.generate("How many boards?")
            else:
                assert await generator.generate("How many boards?") == draft

        assert mocked.await_count == 2
        second_input = mocked.await_args_list[1].kwargs["input"]
        assert any(
            item.get("type") == "function_call_output" and "3 | 5" in item["output"]
            for item in second_input
        )
        for call in mocked.await_args_list:
            assert call.kwargs["max_output_tokens"] == MAX_OUTPUT_TOKENS
            assert call.kwargs["store"] is False
            assert call.kwargs["parallel_tool_calls"] is False


@pytest.mark.asyncio
async def test_reports_sanitized_generation_diagnostics(draft: AnswerDraft) -> None:
    """Aggregate provider usage and accepted lookup behavior.

    Args:
        draft:
            Valid authored draft fixture.
    """

    calls = _response(
        [
            {
                "type": "function_call",
                "id": "fc_1",
                "call_id": "call_1",
                "name": "lookup_references",
                "arguments": '{"source_ids":["BL-PLANS"]}',
                "status": "completed",
            }
        ]
    )

    async with AsyncOpenAI(api_key="synthetic", max_retries=0) as client:
        mocked = AsyncMock(side_effect=[calls, _final(draft)])
        with patch.object(client.responses, "create", mocked):
            diagnostics = await AgentsAnswerGenerator(
                client, "synthetic-model"
            ).generate_with_diagnostics("How many boards?")

    assert diagnostics.draft == draft
    assert diagnostics.model_calls == 2
    assert diagnostics.input_tokens == 200
    assert diagnostics.cached_input_tokens == 40
    assert diagnostics.output_tokens == 20
    assert diagnostics.reasoning_tokens == 10
    assert diagnostics.response_ids == ("resp_synthetic", "resp_synthetic")
    assert diagnostics.source_ids == (SourceId.PLANS,)
    assert diagnostics.lookup_calls == 1


@pytest.mark.parametrize(
    "arguments",
    [
        '{"source_ids":["UNKNOWN"]}',
        '{"source_ids":[]}',
        '{"source_ids":["BL-PLANS","BL-PLANS"]}',
        "invalid json",
    ],
)
@pytest.mark.asyncio
async def test_invalid_tool_arguments_stop_generation(arguments: str) -> None:
    """Fail closed on malformed and invalid tool input.

    Args:
        arguments:
            Synthetic invalid function arguments.
    """

    async with AsyncOpenAI(api_key="synthetic", max_retries=0) as client:
        mocked = AsyncMock(
            return_value=_response(
                [
                    {
                        "type": "function_call",
                        "id": "fc_1",
                        "call_id": "call_1",
                        "name": "lookup_references",
                        "arguments": arguments,
                        "status": "completed",
                    }
                ]
            )
        )
        with (
            patch.object(client.responses, "create", mocked),
            pytest.raises((ModelBehaviorError, UserError)),
        ):
            await AgentsAnswerGenerator(client, "synthetic-model").generate("Hi")

        assert mocked.await_count == 1


@pytest.mark.asyncio
async def test_rejects_draft_without_lookup(draft: AnswerDraft) -> None:
    """Reject fabricated citations when the model skips the tool.

    Args:
        draft:
            Valid authored draft fixture.
    """

    async with AsyncOpenAI(api_key="synthetic", max_retries=0) as client:
        with (
            patch.object(
                client.responses, "create", AsyncMock(return_value=_final(draft))
            ),
            pytest.raises(ValueError, match="lookup tool"),
        ):
            await AgentsAnswerGenerator(client, "synthetic-model").generate("Hi")


def _response(output: list[dict[str, object]]) -> Response:
    """Build a synthetic provider response.

    Args:
        output:
            Responses API output items.

    Returns:
        Typed provider response.
    """

    return Response.model_validate(
        {
            "id": "resp_synthetic",
            "created_at": 0,
            "model": "synthetic-model",
            "object": "response",
            "output": output,
            "parallel_tool_calls": False,
            "tool_choice": "auto",
            "tools": [],
            "status": "completed",
            "usage": {
                "input_tokens": 100,
                "input_tokens_details": {
                    "cache_write_tokens": 0,
                    "cached_tokens": 20,
                },
                "output_tokens": 10,
                "output_tokens_details": {"reasoning_tokens": 5},
                "total_tokens": 110,
            },
        }
    )


def _final(draft: AnswerDraft) -> Response:
    """Build a synthetic structured final response.

    Args:
        draft:
            Draft to serialize into the provider message.

    Returns:
        Typed final provider response.
    """

    return _response(
        [
            {
                "type": "message",
                "id": "msg_1",
                "role": "assistant",
                "status": "completed",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(draft.model_dump(mode="json")),
                        "annotations": [],
                    }
                ],
            }
        ]
    )
