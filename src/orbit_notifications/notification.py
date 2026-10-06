# Copyright 2026-present Orbit Contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Bounded, redacted notification values and an async sender contract."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

_CHANNEL = re.compile(r"[a-z][a-z0-9_-]{0,31}\Z")
_MAX_TARGET_BYTES = 4_096
_MAX_NOTIFICATION_ID_BYTES = 128
_MAX_TITLE_BYTES = 1_024
_MAX_BODY_BYTES = 32 * 1_024


@dataclass(frozen=True, slots=True, repr=False)
class NotificationTarget:
    """One channel-specific address, kept out of representations to protect recipient privacy."""

    channel: str
    address: str = field(repr=False)

    def __post_init__(self) -> None:
        """Validate a bounded channel identifier and opaque control-free destination."""
        if not isinstance(self.channel, str) or _CHANNEL.fullmatch(self.channel) is None:
            raise ValueError("channel must be a lowercase identifier of at most 32 characters.")
        if not isinstance(self.address, str) or not self.address:
            raise ValueError("address must be a non-empty string.")
        if _encoded_size(self.address, "address") > _MAX_TARGET_BYTES or _has_control(self.address):
            raise ValueError("address must be bounded and must not contain control characters.")

    def __repr__(self) -> str:
        """Exclude email addresses, phone numbers, device tokens, and URLs from logs."""
        return f"NotificationTarget(channel={self.channel!r}, address=<redacted>)"


@dataclass(frozen=True, slots=True, repr=False)
class Notification:
    """One bounded plain-text delivery request to one target.

    ``notification_id`` is a caller-supplied correlation value. Adapters may map it to a provider
    idempotency feature, but this contract provides no deduplication or delivery guarantee.
    """

    notification_id: str = field(repr=False)
    target: NotificationTarget = field(repr=False)
    body: str = field(repr=False)
    title: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Validate IDs, target types, and bounded text without retaining mutable values."""
        if (
            not isinstance(self.notification_id, str)
            or not self.notification_id
            or _encoded_size(self.notification_id, "notification_id") > _MAX_NOTIFICATION_ID_BYTES
            or _has_control(self.notification_id)
        ):
            raise ValueError("notification_id must be a bounded, control-free string.")
        if not isinstance(self.target, NotificationTarget):
            raise TypeError("target must be a NotificationTarget.")
        if not isinstance(self.body, str) or not self.body:
            raise ValueError("body must be a non-empty string.")
        if _encoded_size(self.body, "body") > _MAX_BODY_BYTES or _has_control(
            self.body, allow_newline=True
        ):
            raise ValueError("body must be bounded plain text without unsafe control characters.")
        if self.title is not None:
            if not isinstance(self.title, str) or not self.title.strip():
                raise ValueError("title must be a non-empty string or None.")
            if _encoded_size(self.title, "title") > _MAX_TITLE_BYTES or _has_control(self.title):
                raise ValueError("title must be bounded single-line text.")

    def __repr__(self) -> str:
        """Provide useful diagnostics without recipient, notification ID, or message content."""
        return f"Notification(channel={self.target.channel!r}, has_title={self.title is not None})"


@dataclass(frozen=True, slots=True, repr=False)
class NotificationReceipt:
    """Provider acceptance receipt; a returned receipt does not imply device delivery."""

    provider_message_id: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Validate an optional opaque bounded provider identifier."""
        if self.provider_message_id is not None and (
            not isinstance(self.provider_message_id, str)
            or not self.provider_message_id
            or _encoded_size(self.provider_message_id, "provider_message_id") > 512
            or _has_control(self.provider_message_id)
        ):
            raise ValueError("provider_message_id must be bounded and control-free.")

    def __repr__(self) -> str:
        """Keep provider IDs and any embedded correlation data out of diagnostics."""
        return "NotificationReceipt(<redacted>)"


class NotificationSendError(Exception):
    """Safe provider-neutral send failure without recipient or provider SDK details."""

    _message = "Notification send failed."

    def __init__(self) -> None:
        """Use a fixed diagnostic so an adapter cannot accidentally expose provider data."""
        super().__init__(self._message)


class NotificationTemporaryError(NotificationSendError):
    """A potentially temporary send failure; retry safety depends on provider acceptance state."""

    _message = "Notification send failed temporarily."


class NotificationPermanentError(NotificationSendError):
    """A non-retryable failure such as a rejected destination or policy violation."""

    _message = "Notification send failed permanently."


@runtime_checkable
class NotificationSender(Protocol):
    """Async single-target sender contract; implementations own provider resources and shutdown."""

    @property
    def channel(self) -> str:
        """Return the channel identifier accepted by this sender, such as ``email`` or ``sms``."""

    async def send(self, notification: Notification) -> NotificationReceipt:
        """Submit one notification; propagate cancellation and classify known failures safely."""

    async def aclose(self) -> None:
        """Close owned provider resources and reject later sends."""


def _encoded_size(value: str, field_name: str) -> int:
    """Compute UTF-8 size and normalize lone-surrogate failures to safe validation errors."""
    try:
        return len(value.encode("utf-8"))
    except UnicodeEncodeError:
        raise ValueError(f"{field_name} must contain valid Unicode text.") from None


def _has_control(value: str, *, allow_newline: bool = False) -> bool:
    """Reject Unicode control and surrogate categories, allowing LF only in plain-text bodies."""
    for character in value:
        if allow_newline and character == "\n":
            continue
        if unicodedata.category(character) in {"Cc", "Cs"}:
            return True
    return False


__all__ = [
    "Notification",
    "NotificationPermanentError",
    "NotificationReceipt",
    "NotificationSendError",
    "NotificationSender",
    "NotificationTarget",
    "NotificationTemporaryError",
]
