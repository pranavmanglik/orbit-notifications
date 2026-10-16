# Architecture and contract

## Package boundary

`orbit-notifications` is a provider-neutral async capability for sending one plain-text message to
one target. It defines immutable bounded request and receipt values, a sender protocol, and safe
retry-classification error types. It does not include provider SDKs, email formatting, templates,
queues, preferences, consent management, delivery persistence, scheduling, or application
authentication.

```text
Orbit application → NotificationSender capability → channel adapter → delivery provider
       │                    │                            ├── owns SDK/client and credentials
       │                    │                            ├── owns transport and aclose()
       │                    │                            └── maps provider errors safely
       └── owns consent, preferences, retries, and delivery policy
```

`orbit-email` separately defines email message formatting and sender semantics. No email bridge is
included here. An application may adapt an email sender explicitly, but should not assume that
plain-text notification bodies map safely to provider-specific rich email behavior.

## Value and delivery semantics

- A `NotificationTarget` carries an adapter-defined lowercase channel slug and opaque address.
- A `Notification` contains one target, a correlation ID, a non-empty plain-text body, and an
  optional single-line title. UTF-8 byte limits bound identifiers and message content.
- Targets, message content, IDs, and provider message IDs are omitted from normal representations.
- A `NotificationReceipt` means the adapter reports provider acceptance only. It is not proof of
  device delivery, display, or human receipt.
- `notification_id` is not an idempotency key by itself. Provider idempotency is adapter-specific.
- Temporary and permanent errors have fixed generic text and no provider-specific exception chain.

The sender accepts only its declared channel and rejects channel mismatches permanently. It owns
and closes its provider resources through `aclose()`. The application owns sender lifetime,
consent, preferences, retry limits, delivery persistence, and the decision to retry ambiguous
outcomes.

## Dependency direction

Applications depend on the capability and selected channel adapters. Adapters own vendor packages,
credentials, endpoint settings, transport, provider message identifiers, and error mapping. Keep
those integrations out of this package so multiple providers can implement the same one-target
contract.
