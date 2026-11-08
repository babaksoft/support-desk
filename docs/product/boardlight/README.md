# Boardlight product evidence

Boardlight is a fictional SaaS company offering shared task boards for small teams.
People organize tasks in workspaces, each with its own membership and Free or Pro
subscription. All product rules and examples here are authored learning data.

## Reference pack v1

Pack ID: `boardlight-v1`. Source version: `1`. Authored: 2026-11-08.

| Source ID | Document | Coverage |
| --- | --- | --- |
| `BL-PLANS` | [Plans and workspaces](v1/plans.md) | Capacity, ownership, subscription scope |
| `BL-UPGRADES` | [Upgrade behavior](v1/upgrades.md) | Activation, pending payments, delayed display |
| `BL-ACCESS` | [Account access](v1/access.md) | Sign-in, password reset, invitations |
| `BL-TROUBLESHOOTING` | [Basic troubleshooting](v1/troubleshooting.md) | Saving, stale pages, escalation details |

Use a source ID together with its version when citing evidence. IDs remain stable
across revisions; Git tracks edits. Once used in a recorded model/evaluation run,
preserve that pack and create a new version for changed evidence. Keep older
versions available to explain saved results.

The four source documents form the lookup tool's initial corpus. This index and
the [example questions](examples-v1.md) are supporting material, kept outside that
corpus. Examples define expected behavior for human review and future tests;
they are not measured model results.

## Evidence boundaries

The pack supplies general product rules. Customer-specific payment, subscription,
and membership status require authorized account evidence introduced in Stage 4.
Stage 1 can explain checks and ask for missing information. It must distinguish a
customer's report from verified account facts.

Prices, refunds, cancellation, service availability commitments, and enterprise
features are unspecified. Answers about them should state the evidence gap and
refer the question to an operator. Add rules only through a reviewed pack revision.
