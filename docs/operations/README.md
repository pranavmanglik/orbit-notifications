# Orbit Notifications: operations and security

This guide organizes runtime behavior documented by the package. It does not certify production readiness. Verify provider/client versions, permissions, transport security, limits, and failure behavior in the target environment before release.

## Configuration surface

Environment names found in the package README:

The package README does not name `ORBIT_*` variables. Use its typed constructors and application configuration, and confirm exact runtime inputs in the implementation before deployment.

Use the package README's constructor and deployment examples. Store credentials in a secret manager and avoid logging credentials, raw provider errors, request data, or opaque cursors.

## Lifecycle, failure behavior, and limits

`orbit-notifications` defines a provider-neutral async contract for sending one plain-text
notification to one channel-specific target. It is a capability package: it includes no SMS, push,
email provider SDK, queue, or Core dependency. Provider adapters can implement
`NotificationSender` while owning their SDK, credentials, transport, provider failures, and
resource lifecycle.

The package is pre-alpha and supports Python 3.11–3.14:

```bash
python -m pip install orbit-notifications
```

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

## Production validation

Validate startup/shutdown cleanup, timeout and cancellation behavior, concurrency and payload bounds where applicable, secret rotation and least-privilege access, data durability, backup/restore, and failover against the selected provider. Do not infer distributed or durable guarantees from an in-process API or fake-client tests.
