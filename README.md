# Orbit Notifications

`orbit-notifications` defines a provider-neutral async contract for sending one plain-text
notification to one channel-specific target. It is a capability package: it includes no SMS, push,
email provider SDK, queue, or Core dependency. Provider adapters can implement
`NotificationSender` while owning their SDK, credentials, transport, provider failures, and
resource lifecycle.

The package is pre-alpha and supports Python 3.11–3.14:

```bash
python -m pip install orbit-notifications
```

## Contract

```python
from orbit_notifications import Notification, NotificationSender, NotificationTarget


async def deliver(sender: NotificationSender) -> None:
    message = Notification(
        notification_id="invoice-2026-1042",
        target=NotificationTarget(channel="sms", address="+15551234567"),
        title="Invoice ready",
        body="Your invoice is ready to view.",
    )
    try:
        receipt = await sender.send(message)
        print(receipt)
    finally:
        await sender.aclose()
```

The `channel` value is an adapter-defined lowercase identifier. A sender must accept only its
advertised channel, and reject a mismatch with `NotificationPermanentError`. Destinations, IDs,
content, and provider message IDs are excluded from representations. Do not log them unless your
application has an explicit, consent-aware data policy.

## Delivery semantics and security

- One `Notification` contains one recipient, so a send failure has a single-target scope.
- A returned receipt means the adapter reports provider acceptance. It does not mean a person saw
  the notification or that a device received it.
- Send exception strings are fixed generic text; provider diagnostics and addresses should not be
  passed as exception messages or chained into caller-facing errors.
- `notification_id` is a caller-supplied correlation value. It is not an idempotency guarantee.
  Adapters may use provider idempotency keys where supported and must document ambiguous timeouts.
- The capability does not retry. Callers must not blindly retry an ambiguous send; provider adapters
  classify known failures as temporary or permanent and must propagate `asyncio.CancelledError`.
- Titles and bodies are bounded plain text. The package does not render templates, sanitize HTML,
  resolve preferences or consent, batch targets, queue, schedule, or persist deliveries.
- The package has no built-in authentication or delivery store. Treat destinations and content as
  sensitive personal data and apply access control, consent, retention, and redaction at the
  application and provider boundaries.

`orbit-email` separately defines email message formatting and sender semantics. An email adapter for
this contract may compose with `orbit_email.EmailSender`, but neither package imports the other and
no email bridge is included here. Install a channel adapter separately and register its sender
through Core's dependency container when the application needs that channel.

## Documentation

The package-specific guides cover [architecture](docs/architecture/overview.md), [operations and security](docs/operations/README.md), and [development](docs/development/README.md), with [security guidance](docs/security/overview.md). The [documentation index](docs/README.md) links to the full package overview and project policies.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
ruff format --check .
mypy
python -m build
```

Tests use deterministic fake senders. No provider, queue, or delivery behavior is included or
verified.

Licensed under Apache-2.0.

