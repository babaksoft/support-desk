# Slice 1.4: provenance around nondeterministic generation

## Hypothesis

Recording a started attempt before inference and finalizing it afterward should make
successes and failures explainable without keeping a database transaction open during
an unpredictable model call. A client-owned idempotency key should prevent a repeated
submission from making another model call.

## Comparison and evidence

The previous process returned a draft or safe HTTP failure but retained no durable
business evidence. The new repository creates an interaction and started attempt in
one short transaction, performs generation without a transaction, then records a
successful draft or a stable failure category in another transaction. Model identity,
timestamps, retry linkage, and versioned evidence establish provenance. Provider
exception text is deliberately excluded.

Deterministic service tests showed that an identical successful submission replays
the stored draft with one generator call. A failure test recorded only `failed`, then
linked a successful explicit retry. Disposable PostgreSQL tests applied, inspected,
reverted, and reapplied the baseline migration; they also round-tripped successful
evidence, rejected an invalid retry, and deleted a retention-expired interaction.

## Conclusion

The two-transaction boundary preserves an observable attempt even when generation
fails while avoiding a long-lived database transaction. Idempotency belongs to the
authenticated request, not to question text: a new submission UUID means a new
billable attempt, while an identical UUID replays its durable outcome. Retry linkage
is explicit so a later operator view can distinguish retries from unrelated repeated
questions. Cloud durability and automatic retention scheduling remain separate work.
