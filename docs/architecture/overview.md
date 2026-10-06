# Orbit Notifications: architecture and boundaries

## Responsibility

`orbit-notifications` defines a provider-neutral async contract for sending one plain-text
notification to one channel-specific target. It is a capability package: it includes no SMS, push,
email provider SDK, queue, or Core dependency. Provider adapters can implement
`NotificationSender` while owning their SDK, credentials, transport, provider failures, and
resource lifecycle.

The package is pre-alpha and supports Python 3.11–3.14:

```bash
python -m pip install orbit-notifications
```

## Declared dependencies

The following dependency declarations come from the checked-in manifests. Optional groups and development dependencies are called out separately.

### `pyproject.toml`
- No dependencies declared.
- Optional `dev` group: `pytest>=8,<10`, `pytest-asyncio>=0.24,<2`, `ruff>=0.8,<1`, `mypy>=1.13,<2`, `build>=1.2,<2`.

Declared dependencies do not mean that optional providers or services are bundled with this package.

## Implementation layout

Representative implementation files in this checkout:

- `src/orbit_notifications/__init__.py`
- `src/orbit_notifications/notification.py`

## Public contract and scope

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

## Boundary rules

Keep provider SDKs, credentials, transports, and provider-specific error translation in provider adapters. Keep reusable capability contracts in the matching capability package and lifecycle orchestration in Core. Apply the relevant layer for this repository and preserve the dependency direction shown above.
