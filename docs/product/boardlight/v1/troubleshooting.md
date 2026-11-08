# Basic troubleshooting

Source ID: `BL-TROUBLESHOOTING`

Version: `1`

## Saving tasks

Boardlight requires an internet connection to save changes. A task edit shows
Saving while the request is in progress, Saved after confirmation, or Save failed
when the request fails. Treat Saved as the confirmation that a change was stored.

If saving fails, copy any unsaved task text, check the internet connection, and
retry the save. Preserve unsaved text before reloading or signing out. If the
problem continues, report the workspace ID, board name, error, and occurrence time
with timezone to an operator. Share only the task content needed for diagnosis.

## Stale workspace information

Check the current workspace name and ID before comparing plans or board contents.
After preserving unsaved text, reload the page to fetch current information.
For Free still displayed after an upgrade, follow the payment and activation checks
in [Upgrade behavior](upgrades.md#free-still-displayed-after-an-upgrade).

## Support evidence

Use the exact visible error and relevant times to describe a problem. Remove
passwords, links granting account access, and payment details from shared screenshots.
An observed save failure alone does not establish a service-wide outage or its
cause; an operator needs further evidence to diagnose it.
