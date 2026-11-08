# Upgrade behavior

Source ID: `BL-UPGRADES`

Version: `1`

## Upgrade and activation

The workspace owner opens Settings, then Billing, confirms the workspace name and
ID, and selects Pro. Billing shows a payment status of Pending, Failed, or Succeeded.
A Pending or Failed payment leaves the workspace on its current plan.

After Billing shows Succeeded, Pro limits should become available within 10 minutes.
The activation window starts at the successful payment confirmation time. A receipt
or payment claim alone does not establish the workspace's current subscription state.

## Free still displayed after an upgrade

1. Confirm the workspace ID matches the workspace selected for the upgrade.
2. Ask the owner to check the payment status in that workspace's Billing page.
3. If Pending, check again later; if Failed, the owner should follow the payment
   error shown in Billing. Neither status confirms a completed upgrade.
4. If Succeeded less than 10 minutes ago, allow the remaining activation time and
   reload the page after preserving any unsaved task text.
5. If Succeeded at least 10 minutes ago and Free is still displayed after reloading,
   ask an operator to investigate the activation delay.

The operator needs the workspace ID, reported payment status, successful payment
confirmation time with timezone, and any visible error. Treat workspace mismatch,
pending payment, and activation delay as possibilities until account evidence
establishes the cause.

## Investigation scope

An activation investigation verifies the payment and subscription records for the
authorized workspace. Guidance based on this document can explain the process;
only account evidence can establish whether a specific upgrade succeeded or why
it is delayed. The operator reviews the proposed response before use.
