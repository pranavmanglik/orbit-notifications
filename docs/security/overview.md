# Orbit Notifications: security

## Package-specific security guidance

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

## Credentials and sensitive data

Use least-privilege credentials and a secret manager for provider secrets. Do not commit secrets, tokens, private keys, personal data, request bodies, raw provider errors, or opaque cursors. Enable TLS certificate verification for remote services unless package documentation gives a narrowly scoped local-development exception.

## Vulnerability disclosure

Follow the repository [security policy](../../SECURITY.md). Do not post vulnerability details in public issues. The policy describes private reporting alternatives without claiming that a hosting-platform setting is enabled.

## Limits

This page records source and package documentation, not an independent security audit. Validate the package, its provider SDKs, and its deployment configuration before production use.
