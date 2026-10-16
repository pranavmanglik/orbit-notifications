# Security and privacy

## Recipient and message data

Destinations, message bodies, titles, correlation IDs, and provider message IDs may contain
personal or confidential data. Their fields are hidden from ordinary `repr()` output, but this is
only a defense against accidental display; it does not redact logging performed by adapters,
tracing hooks, debuggers, crash dumps, or application code. Do not log complete request or receipt
objects, addresses, message content, provider responses, or correlation identifiers by default.

Apply purpose limitation, consent and preference checks, access control, retention, deletion, and
regional data requirements in the application and provider integration. This package does not
make consent decisions or store an audit trail. Review provider retention, support access, data
residency, and deletion semantics before sending sensitive content.

## Content and transport

Titles and bodies are bounded plain text. The package does not render templates or sanitize HTML;
adapters must not silently reinterpret content as markup. Validate channel-specific addresses and
policy before provider submission. Keep test destinations separate from real recipient lists.

The selected adapter owns authentication, authorization, TLS, credential storage and rotation,
network timeouts, and provider-side message handling. Use supported workload identity or a secret
manager, grant least privilege, verify TLS certificates, and avoid exposing credentials in
configuration output or diagnostics. Restrict access to queues and delivery receipts if an
application adds durable delivery state.

## Safe failures

The capability's exception messages are fixed and omit destination, content, and raw vendor error
details. Adapters should preserve this property when translating failures, avoid chaining
unsanitized provider exceptions, and emit only reviewed bounded diagnostic categories. An
application may need richer diagnostics, but should store them in access-controlled systems after
redaction rather than attaching them to caller-facing exceptions.

## Vulnerability reporting

Use the private process described in the repository [security policy](../../SECURITY.md) to report
suspected vulnerabilities.
