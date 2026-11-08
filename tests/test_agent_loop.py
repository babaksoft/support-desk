"""Exercise the real SDK loop using synthetic provider responses."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from agents import ModelBehaviorError, UserError
from openai import AsyncOpenAI
from openai.types.responses import Response

from support_desk.domain import AnswerDraft, SourceId
from support_desk.infrastructure import AgentsAnswerGenerator, ReferenceLookup


@pytest.mark.parametrize("scenario", ["answered", "insufficient", "unread_source"])
def test_sdk_executes_tool_and_validates_draft(
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

    asyncio.run(_exercise_sdk_loop(calls, final, draft, scenario))


@pytest.mark.parametrize(
    "arguments",
    [
        '{"source_ids":["UNKNOWN"]}',
        '{"source_ids":[]}',
        '{"source_ids":["BL-PLANS","BL-PLANS"]}',
        "invalid json",
    ],
)
def test_invalid_tool_arguments_stop_generation(arguments: str) -> None:
    """Fail closed on malformed and invalid tool input.

    Args:
        arguments:
            Synthetic invalid function arguments.
    """

    asyncio.run(_exercise_invalid_arguments(arguments))


def test_rejects_draft_without_lookup(draft: AnswerDraft) -> None:
    """Reject fabricated citations when the model skips the tool.

    Args:
        draft:
            Valid authored draft fixture.
    """

    asyncio.run(_exercise_missing_lookup(draft))


def test_tool_budget_is_enforced() -> None:
    """Stop reference execution after two calls."""

    lookup = ReferenceLookup()
    lookup.lookup([SourceId.PLANS])
    lookup.lookup([SourceId.UPGRADES])
    with pytest.raises(ValueError, match="limit"):
        lookup.lookup([SourceId.ACCESS])
    assert SourceId.ACCESS not in lookup.seen


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


async def _exercise_sdk_loop(
    calls: Response, final: Response, draft: AnswerDraft, scenario: str
) -> None:
    """Run synthetic provider responses and inspect the tool result.

    Args:
        calls:
            Synthetic tool-call response.
        final:
            Synthetic final answer response.
        draft:
            Expected generated draft.
        scenario:
            Answer or evidence-validation scenario.
    """

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
            assert call.kwargs["max_output_tokens"] == 1024
            assert call.kwargs["store"] is False
            assert call.kwargs["parallel_tool_calls"] is False


async def _exercise_invalid_arguments(arguments: str) -> None:
    """Run a synthetic function call through SDK argument validation.

    Args:
        arguments:
            Invalid synthetic function arguments.
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


async def _exercise_missing_lookup(draft: AnswerDraft) -> None:
    """Return a synthetic final response before any reference lookup.

    Args:
        draft:
            Synthetic draft returned before evidence lookup.
    """

    async with AsyncOpenAI(api_key="synthetic", max_retries=0) as client:
        with (
            patch.object(
                client.responses, "create", AsyncMock(return_value=_final(draft))
            ),
            pytest.raises(ValueError, match="lookup tool"),
        ):
            await AgentsAnswerGenerator(client, "synthetic-model").generate("Hi")
