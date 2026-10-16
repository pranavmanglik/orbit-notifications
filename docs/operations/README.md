# Operations

`NotificationSender` sends one notification to one target. There is no queue, scheduler, retry
loop, delivery database, or batch API. The application creates the sender, owns when a delivery is
attempted, and calls `aclose()` when no more sends should be accepted.

## Delivery and retries

A successful `send()` returns a `NotificationReceipt` indicating provider acceptance. Delivery to
a handset, inbox, or person may happen later or may fail. A timeout can be ambiguous: the provider
may have accepted the send even though the application did not receive the response. The
correlation `notification_id` does not guarantee deduplication. Retry an ambiguous request only if
the adapter documents a provider idempotency mechanism or the application accepts possible
duplicates.

Adapters classify known transient conditions as `NotificationTemporaryError` and known
non-retryable conditions as `NotificationPermanentError`. This package never retries automatically.
The application should apply bounded attempts, backoff with jitter, per-target rate limits, and a
clear dead-letter or operator recovery path where needed. Do not retry permanent validation,
authorization, or consent failures. Preserve `asyncio.CancelledError` so shutdown and caller
cancellation remain effective.

## Lifecycle and capacity

The adapter owns connection pools, SDK clients, and background workers. Use its documented
timeouts, concurrency limits, quotas, and async lifecycle. Close senders during application
shutdown and do not share one sender across event loops unless its adapter explicitly supports
that use. If the application adds a durable queue, define delivery state transitions, duplicate
handling, queue retention, and poison-message behavior there.

## Content and channel constraints

The request accepts one target. Channels are lowercase adapter-defined identifiers; install a
sender that advertises the requested channel. The package bounds the UTF-8 address to 4,096 bytes,
correlation ID to 128 bytes, title to 1,024 bytes, and body to 32 KiB. Bodies permit line feeds but
reject other control characters. These are contract limits, not guarantees that the provider
accepts every target or message. Respect provider-specific destination formats, segment limits,
quotas, template rules, and regional restrictions.

## Operational checks

Validate connection and send timeouts, cancellation during network calls, provider outages,
ambiguous acceptance, throttling, credential rotation, shutdown with in-flight requests, duplicate
handling, and provider quota exhaustion using a dedicated test account. Do not send test
notifications to real recipients without an approved test target and consent.
