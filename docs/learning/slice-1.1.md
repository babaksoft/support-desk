# Bounded evidence and the agent tool loop

Hypothesis: typed tool arguments, a fixed reference pack, and post-generation
citation validation can reject malformed calls and fabricated source identities
before a draft reaches the operator.

Comparison: synthetic provider responses drive the actual Agents SDK loop through
a valid lookup and answer, an evidence-gap response, invalid arguments, a skipped
lookup, and a citation to a source that was not returned. API tests separately
exercise admission, cancellation, deadlines, input bounds, and safe failure output.

Evidence: `tests/infrastructure/test_agent.py` and
`tests/api/routes/test_questions.py` exercise these paths deterministically. Focused
domain, application, middleware, and composition tests cover invariants, deadlines,
request streaming, and explicit provider settings.
`tests/test_architecture.py` recursively checks inner dependencies and verifies that
runtime evidence matches the reviewed Markdown. The packaged evidence copy keeps
installed wheels independent of a repository checkout; the parity check guards
against drift.

Conclusion: schema and source-membership checks enforce structural contracts.
They do not prove that a claim follows from a citation or that an evidence-gap
decision is appropriate. Those require the budgeted model smoke run, authored
examples, and later evaluation/human review. Fake provider responses establish SDK
wiring, not model quality or live provider compatibility.

Operational choice: requests use one process-local admission slot, bounded turns,
tool calls, output tokens, and deadlines. The provider client has zero automatic
retries. An explicit retry is a new billable attempt; persistence and attempt
identity arrive later. Traces are disabled until the planned exporter/privacy
work; Responses requests set `store=False`. Neither setting guarantees provider
zero retention or cancellation of remote computation.

Lifecycle choice: FastAPI owns generic process-resource orchestration through its
constructor lifespan. Composition registers the OpenAI async client only when
inference is enabled, and the API releases registered resources in reverse startup
order. Direct asynchronous behavior is tested with pytest-asyncio; private helpers
remain limited to synthetic inputs and fake behavior.

SDK verification: Python 3.12 resolves `openai-agents` 0.24.0 and `openai` 3.46.0.
Implementation was checked against installed signatures and official
[quickstart](https://developers.openai.com/api/docs/guides/agents/quickstart?lang=python),
[running agents](https://developers.openai.com/api/docs/guides/agents/running-agents),
and [tracing controls](https://developers.openai.com/api/docs/guides/agents/integrations-observability).
