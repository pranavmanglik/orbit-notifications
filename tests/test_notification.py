from __future__ import annotations

import pytest

from orbit_notifications import (
    Notification,
    NotificationPermanentError,
    NotificationReceipt,
    NotificationSender,
    NotificationSendError,
    NotificationTarget,
    NotificationTemporaryError,
)


def notification(
    *,
    target: NotificationTarget | None = None,
    title: str | None = "Invoice ready",
    body: str = "Your invoice is ready to view.",
    notification_id: str = "invoice-1042",
) -> Notification:
    return Notification(
        notification_id=notification_id,
        target=target or NotificationTarget("sms", "+15551234567"),
        title=title,
        body=body,
    )


def test_validates_target_and_redacts_address() -> None:
    target = NotificationTarget("push_web", "https://push.example.test/subscription-secret")
    assert target.channel == "push_web"
    assert "subscription-secret" not in repr(target)
    assert "push_web" in repr(target)


@pytest.mark.parametrize("channel", ["", "SMS", "sms.provider", "bad channel", "-sms", "a" * 33])
def test_rejects_invalid_channel(channel: str) -> None:
    with pytest.raises(ValueError, match="channel"):
        NotificationTarget(channel, "destination")


@pytest.mark.parametrize("address", ["", "phone\nBcc:attacker", "token\x00value", "\ud800"])
def test_rejects_invalid_or_controlled_address(address: str) -> None:
    with pytest.raises(ValueError, match="address"):
        NotificationTarget("email", address)


def test_notification_allows_plain_text_newlines_and_redacts_sensitive_values() -> None:
    item = notification(body="Line one.\nLine two.")
    representation = repr(item)
    assert "sms" in representation
    assert "invoice-1042" not in representation
    assert "+15551234567" not in representation
    assert "Invoice ready" not in representation
    assert "Line one" not in representation


@pytest.mark.parametrize(
    "kwargs",
    [
        {"notification_id": ""},
        {"notification_id": "bad\nkey"},
        {"body": ""},
        {"body": "unsafe\x00text"},
        {"body": "bad\ud800unicode"},
        {"title": "two\nlines"},
        {"title": "  "},
    ],
)
def test_rejects_invalid_notification_values(kwargs: dict[str, object]) -> None:
    values: dict[str, object] = {
        "notification_id": "invoice-1042",
        "target": NotificationTarget("sms", "+15551234567"),
        "body": "Your invoice is ready.",
        "title": "Invoice ready",
    }
    values.update(kwargs)
    with pytest.raises(ValueError):
        Notification(**values)  # type: ignore[arg-type]


def test_enforces_utf8_byte_limits() -> None:
    with pytest.raises(ValueError, match="address"):
        NotificationTarget("push", "é" * 2_049)
    with pytest.raises(ValueError, match="title"):
        notification(title="é" * 513)
    with pytest.raises(ValueError, match="body"):
        notification(body="x" * (32 * 1_024 + 1))


def test_receipt_is_redacted_and_validates_provider_id() -> None:
    receipt = NotificationReceipt("provider-account-id-123")
    assert "provider-account-id-123" not in repr(receipt)
    assert repr(receipt) == "NotificationReceipt(<redacted>)"
    with pytest.raises(ValueError, match="provider_message_id"):
        NotificationReceipt("bad\nid")


@pytest.mark.asyncio
async def test_sender_protocol_exposes_single_target_send_and_lifecycle() -> None:
    class FakeSender:
        channel = "sms"

        def __init__(self) -> None:
            self.closed = False

        async def send(self, item: Notification) -> NotificationReceipt:
            assert item.target.channel == self.channel
            return NotificationReceipt("opaque-provider-id")

        async def aclose(self) -> None:
            self.closed = True

    sender = FakeSender()
    assert isinstance(sender, NotificationSender)
    receipt = await sender.send(notification())
    assert isinstance(receipt, NotificationReceipt)
    await sender.aclose()
    assert sender.closed


def test_send_failures_share_base_type_and_preserve_retry_classification() -> None:
    assert issubclass(NotificationTemporaryError, NotificationSendError)
    assert issubclass(NotificationPermanentError, NotificationSendError)
    assert NotificationTemporaryError is not NotificationPermanentError
    assert str(NotificationTemporaryError()) == "Notification send failed temporarily."
    assert str(NotificationPermanentError()) == "Notification send failed permanently."
    with pytest.raises(TypeError):
        NotificationTemporaryError("provider-token")  # type: ignore[call-arg]
