"""Run the explicitly approved Slice 1.1 paid model smoke experiment."""

import argparse
import asyncio
import json
import os
from decimal import Decimal
from time import monotonic
from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field

from support_desk.domain import SourceId
from support_desk.infrastructure import AgentsAnswerGenerator, GenerationDiagnostics

MODEL_ID: Literal["gpt-5.4-mini-2026-03-17"] = "gpt-5.4-mini-2026-03-17"
EXPERIMENT_ID: Literal["slice-1.1-model-smoke-v1-follow-up"] = (
    "slice-1.1-model-smoke-v1-follow-up"
)
INPUT_PRICE_PER_MILLION = Decimal("0.75")
CACHED_INPUT_PRICE_PER_MILLION = Decimal("0.075")
OUTPUT_PRICE_PER_MILLION = Decimal("4.50")
EXPERIMENT_BUDGET_USD = Decimal("0.10")
QUESTION_TIMEOUT_SECONDS = 45.0
MAX_EXPERIMENT_MODEL_CALLS = 6
MAX_EXPERIMENT_OUTPUT_TOKENS = 6_144


class SmokeQuestion(BaseModel):
    """Define one authored paid smoke case.

    Attributes:
        case_id:
            Stable authored case identifier.
        question:
            Product question sent to the agent.
        expected_status:
            Required draft status.
        expected_source_ids:
            Required cited source identifiers.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    case_id: str = Field(description="Stable authored case identifier.")
    question: str = Field(description="Product question sent to the agent.")
    expected_status: Literal["answered", "insufficient_evidence"] = Field(
        description="Required draft status."
    )
    expected_source_ids: tuple[SourceId, ...] = Field(
        description="Required cited source identifiers."
    )


class SmokeCaseResult(BaseModel):
    """Record sanitized evidence for one paid smoke case.

    Attributes:
        case_id:
            Stable authored case identifier.
        question:
            Product question sent to the agent.
        status:
            Validated draft status.
        answer:
            Unreviewed generated answer.
        evidence:
            Source identifiers cited by the draft.
        returned_sources:
            Sources returned by the lookup tool.
        lookup_calls:
            Number of accepted lookup tool calls.
        model_calls:
            Number of provider model calls.
        input_tokens:
            Total input tokens across model calls.
        cached_input_tokens:
            Input tokens served from the provider cache.
        output_tokens:
            Total output tokens, including reasoning tokens.
        reasoning_tokens:
            Reasoning tokens included in the output total.
        response_ids:
            Provider response identifiers for audit lookup.
        latency_seconds:
            End-to-end agent-run duration.
        estimated_cost_usd:
            Estimated standard token cost in US dollars.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    case_id: str = Field(description="Stable authored case identifier.")
    question: str = Field(description="Product question sent to the agent.")
    status: Literal["answered", "insufficient_evidence"] = Field(
        description="Validated draft status."
    )
    answer: str = Field(description="Unreviewed generated answer.")
    evidence: tuple[SourceId, ...] = Field(
        description="Source identifiers cited by the draft."
    )
    returned_sources: tuple[SourceId, ...] = Field(
        description="Sources returned by the lookup tool."
    )
    lookup_calls: int = Field(description="Number of accepted lookup tool calls.")
    model_calls: int = Field(description="Number of provider model calls.")
    input_tokens: int = Field(description="Total input tokens across model calls.")
    cached_input_tokens: int = Field(
        description="Input tokens served from the provider cache."
    )
    output_tokens: int = Field(
        description="Total output tokens, including reasoning tokens."
    )
    reasoning_tokens: int = Field(
        description="Reasoning tokens included in the output total."
    )
    response_ids: tuple[str, ...] = Field(
        description="Provider response identifiers for audit lookup."
    )
    latency_seconds: float = Field(description="End-to-end agent-run duration.")
    estimated_cost_usd: str = Field(
        description="Estimated standard token cost in US dollars."
    )


class SmokeReport(BaseModel):
    """Record the complete bounded paid smoke result.

    Attributes:
        experiment:
            Stable experiment name.
        model:
            Explicit provider model snapshot.
        evidence_version:
            Authored product evidence version.
        cases:
            Sanitized case results.
        model_calls:
            Total provider model calls.
        input_tokens:
            Total input tokens across cases.
        cached_input_tokens:
            Total cached input tokens across cases.
        output_tokens:
            Total output tokens across cases.
        estimated_cost_usd:
            Estimated standard token cost in US dollars.
        budget_usd:
            Approved experiment budget in US dollars.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    experiment: Literal["slice-1.1-model-smoke-v1-follow-up"] = Field(
        description="Stable experiment name."
    )
    model: Literal["gpt-5.4-mini-2026-03-17"] = Field(
        description="Explicit provider model snapshot."
    )
    evidence_version: Literal["boardlight-v1"] = Field(
        description="Authored product evidence version."
    )
    cases: tuple[SmokeCaseResult, ...] = Field(description="Sanitized case results.")
    model_calls: int = Field(description="Total provider model calls.")
    input_tokens: int = Field(description="Total input tokens across cases.")
    cached_input_tokens: int = Field(
        description="Total cached input tokens across cases."
    )
    output_tokens: int = Field(description="Total output tokens across cases.")
    estimated_cost_usd: str = Field(
        description="Estimated standard token cost in US dollars."
    )
    budget_usd: Literal["0.10"] = Field(
        description="Approved experiment budget in US dollars."
    )


SMOKE_QUESTIONS = (
    SmokeQuestion(
        case_id="board-capacity",
        question="How many boards can a Free workspace have?",
        expected_status="answered",
        expected_source_ids=(SourceId.PLANS,),
    ),
    SmokeQuestion(
        case_id="refund-policy",
        question="Can I get a refund if I cancel Pro tomorrow?",
        expected_status="insufficient_evidence",
        expected_source_ids=(),
    ),
)


async def run_smoke(case_id: str | None = None) -> SmokeReport:
    """Run two bounded authored cases through the live provider.

    Args:
        case_id:
            Optional single case to resume after a previous case attempt.

    Returns:
        Sanitized experiment result.

    Raises:
        RuntimeError:
            Required settings, expected behavior, or experiment limits are invalid.
    """

    if os.environ.get("SUPPORT_DESK_ENABLE_INFERENCE") != "1":
        raise RuntimeError("Paid inference is not explicitly enabled.")
    if os.environ.get("SUPPORT_DESK_MODEL") != MODEL_ID:
        raise RuntimeError("The configured model does not match the approved snapshot.")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("The provider credential is unavailable.")

    results: list[SmokeCaseResult] = []
    async with AsyncOpenAI(api_key=api_key, max_retries=0, timeout=40) as client:
        generator = AgentsAnswerGenerator(client, MODEL_ID)
        for question in _select_questions(case_id):
            started_at = monotonic()
            async with asyncio.timeout(QUESTION_TIMEOUT_SECONDS):
                diagnostics = await generator.generate_with_diagnostics(
                    question.question
                )
            result = _build_case_result(question, diagnostics, monotonic() - started_at)
            print(
                json.dumps(
                    {
                        "event": "case_completed",
                        "result": result.model_dump(mode="json"),
                    },
                    sort_keys=True,
                ),
                flush=True,
            )
            _verify_case(question, result)
            results.append(result)

    report = _build_report(results)
    _verify_experiment_limits(report)

    return report


def main() -> None:
    """Run the experiment and print only sanitized JSON evidence."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case-id",
        choices=tuple(question.case_id for question in SMOKE_QUESTIONS),
        help="Run one remaining authored case without retrying earlier attempts.",
    )
    arguments = parser.parse_args()
    try:
        report = asyncio.run(run_smoke(arguments.case_id))
    except Exception as error:
        print(
            json.dumps(
                {
                    "experiment": EXPERIMENT_ID,
                    "status": "failed",
                    "error_type": type(error).__name__,
                },
                sort_keys=True,
            )
        )
        raise SystemExit(1) from None

    print(report.model_dump_json(indent=2))


def _build_case_result(
    question: SmokeQuestion,
    diagnostics: GenerationDiagnostics,
    latency_seconds: float,
) -> SmokeCaseResult:
    """Build sanitized evidence for one completed case.

    Args:
        question:
            Authored smoke case.
        diagnostics:
            Provider and tool evidence from the agent run.
        latency_seconds:
            End-to-end run duration.

    Returns:
        Sanitized case result.
    """

    cost = _estimate_cost(diagnostics)
    return SmokeCaseResult(
        case_id=question.case_id,
        question=question.question,
        status=diagnostics.draft.status,
        answer=diagnostics.draft.answer,
        evidence=tuple(item.source_id for item in diagnostics.draft.evidence),
        returned_sources=diagnostics.source_ids,
        lookup_calls=diagnostics.lookup_calls,
        model_calls=diagnostics.model_calls,
        input_tokens=diagnostics.input_tokens,
        cached_input_tokens=diagnostics.cached_input_tokens,
        output_tokens=diagnostics.output_tokens,
        reasoning_tokens=diagnostics.reasoning_tokens,
        response_ids=diagnostics.response_ids,
        latency_seconds=round(latency_seconds, 3),
        estimated_cost_usd=_format_cost(cost),
    )


def _select_questions(case_id: str | None) -> tuple[SmokeQuestion, ...]:
    """Select the full experiment or one remaining authored case.

    Args:
        case_id:
            Optional stable case identifier.

    Returns:
        Authored cases to attempt.

    Raises:
        RuntimeError:
            The requested case identifier is unknown.
    """

    if case_id is None:
        return SMOKE_QUESTIONS

    selected = tuple(
        question for question in SMOKE_QUESTIONS if question.case_id == case_id
    )
    if not selected:
        raise RuntimeError("The requested smoke case is unknown.")

    return selected


def _build_report(results: list[SmokeCaseResult]) -> SmokeReport:
    """Aggregate sanitized case evidence.

    Args:
        results:
            Completed smoke case results.

    Returns:
        Complete experiment report.
    """

    total_cost = sum(
        (Decimal(result.estimated_cost_usd) for result in results), Decimal()
    )
    return SmokeReport(
        experiment=EXPERIMENT_ID,
        model=MODEL_ID,
        evidence_version="boardlight-v1",
        cases=tuple(results),
        model_calls=sum(result.model_calls for result in results),
        input_tokens=sum(result.input_tokens for result in results),
        cached_input_tokens=sum(result.cached_input_tokens for result in results),
        output_tokens=sum(result.output_tokens for result in results),
        estimated_cost_usd=_format_cost(total_cost),
        budget_usd="0.10",
    )


def _verify_case(question: SmokeQuestion, result: SmokeCaseResult) -> None:
    """Require the authored outcome and bounded per-case behavior.

    Args:
        question:
            Authored smoke case.
        result:
            Sanitized case result.

    Raises:
        RuntimeError:
            The result violates an authored expectation or executable limit.
    """

    if result.status != question.expected_status:
        raise RuntimeError("The draft status did not match the authored expectation.")
    if result.evidence != question.expected_source_ids:
        raise RuntimeError("The draft evidence did not match the authored expectation.")
    if not 1 <= result.lookup_calls <= 2:
        raise RuntimeError("The lookup call count exceeded its executable bounds.")
    if not 1 <= result.model_calls <= 3:
        raise RuntimeError("The model call count exceeded its executable bounds.")
    if result.output_tokens > 3_072:
        raise RuntimeError("The case output exceeded its executable token bound.")


def _verify_experiment_limits(report: SmokeReport) -> None:
    """Require the approved aggregate experiment limits.

    Args:
        report:
            Complete experiment report.

    Raises:
        RuntimeError:
            The report exceeds an approved experiment limit.
    """

    if report.model_calls > MAX_EXPERIMENT_MODEL_CALLS:
        raise RuntimeError("The experiment model call limit was exceeded.")
    if report.output_tokens > MAX_EXPERIMENT_OUTPUT_TOKENS:
        raise RuntimeError("The experiment output token limit was exceeded.")
    if Decimal(report.estimated_cost_usd) > EXPERIMENT_BUDGET_USD:
        raise RuntimeError("The estimated experiment cost exceeded its budget.")


def _estimate_cost(diagnostics: GenerationDiagnostics) -> Decimal:
    """Estimate standard token cost from provider-reported usage.

    Args:
        diagnostics:
            Provider usage from one agent run.

    Returns:
        Estimated cost in US dollars.
    """

    uncached_input_tokens = max(
        diagnostics.input_tokens - diagnostics.cached_input_tokens, 0
    )
    return (
        Decimal(uncached_input_tokens) * INPUT_PRICE_PER_MILLION
        + Decimal(diagnostics.cached_input_tokens) * CACHED_INPUT_PRICE_PER_MILLION
        + Decimal(diagnostics.output_tokens) * OUTPUT_PRICE_PER_MILLION
    ) / Decimal(1_000_000)


def _format_cost(cost: Decimal) -> str:
    """Format an estimated cost without binary floating-point conversion.

    Args:
        cost:
            Estimated cost in US dollars.

    Returns:
        Cost rounded to eight decimal places.
    """

    return str(cost.quantize(Decimal("0.00000001")))


if __name__ == "__main__":
    main()
