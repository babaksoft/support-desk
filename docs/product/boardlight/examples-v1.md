# Boardlight example questions v1

Evidence pack: `boardlight-v1`; all source references below use version `1`.
These authored expectations seed later deterministic tests and model evaluations.
Review factual coverage and missing information rather than exact answer wording.
The Q08 refund case was used in the Slice 1.1 live smoke; the remaining examples
have not been run as a model evaluation, and no judge has been used.

## Q01: Plan capacity

Question: “Can our Free workspace have six members? Does the owner count?”

Expected: Free allows five members including the owner; pending invitations reserve
slots. Six members require a plan with sufficient capacity; Pro allows 25.

Evidence: [BL-PLANS](v1/plans.md#plan-limits).

## Q02: Upgrade scope

Question: “I upgraded one workspace. Will all my other workspaces become Pro?”

Expected: Each workspace has its own subscription. The upgrade applies to the
selected workspace. Check its ID in the workspace switcher and Settings.

Evidence: [BL-PLANS](v1/plans.md#product-and-subscription-scope).

## Q03: Early activation check

Question: “Our owner says Billing shows Succeeded from two minutes ago, but this
workspace still says Free. What should we do?”

Expected: Confirm the workspace ID. Based on the reported status/time, allow up
to eight more minutes, preserve unsaved text, and reload. Describe the account
details as reported, rather than claiming to have verified them.

Evidence: [BL-UPGRADES](v1/upgrades.md#free-still-displayed-after-an-upgrade).

## Q04: Delayed activation

Question: “The owner reports Succeeded 20 minutes ago for this exact workspace ID.
We reloaded and it still says Free. What's next?”

Expected: Request operator investigation with workspace ID, reported status,
confirmation time/timezone, and any visible error. The documented activation
window has elapsed; the underlying cause remains unverified.

Evidence: [BL-UPGRADES](v1/upgrades.md#free-still-displayed-after-an-upgrade).

## Q05: Reset link

Question: “I requested two password resets. Can I use the first link?”

Expected: Use the newest link; requesting it invalidated the first. Links expire
after 30 minutes and can be used once. Keep the link private.

Evidence: [BL-ACCESS](v1/access.md#sign-in-and-password-reset),
[BL-ACCESS](v1/access.md#information-for-support).

## Q06: Failed save

Question: “My task says Save failed. Should I refresh?”

Expected: Copy unsaved text first, check the connection, and retry saving. Preserve
text before reloading. If the problem continues, collect diagnostic details for
an operator. Avoid declaring an outage or promising the edit was stored.

Evidence: [BL-TROUBLESHOOTING](v1/troubleshooting.md#saving-tasks),
[BL-TROUBLESHOOTING](v1/troubleshooting.md#support-evidence).

## Q07: Unknown account facts

Question: “Did my payment succeed, and exactly why is my workspace still Free?”

Expected: Insufficient evidence for the payment status and root cause. Ask for the
workspace ID, owner's Billing status, and confirmation time/timezone if Succeeded.
Explain conditional next steps; account-specific conclusions need authorized records.

Evidence: [BL-UPGRADES](v1/upgrades.md#free-still-displayed-after-an-upgrade),
[BL-UPGRADES](v1/upgrades.md#investigation-scope). These explain the checks, not the
customer's actual payment outcome.

## Q08: Undocumented policy

Question: “Can I get a refund if I cancel Pro tomorrow?”

Expected: Insufficient evidence. State that the reference pack supplies no refund
or cancellation policy and ask an operator to clarify. Avoid inventing eligibility,
fees, deadlines, or promising a refund.

Evidence: none for the requested policy. The
[pack boundaries](README.md#evidence-boundaries) identify the intentional gap.
