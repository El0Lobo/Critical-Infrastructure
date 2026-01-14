"""Project-level wrappers around django-encrypted-model-fields with safe fallbacks."""

from encrypted_model_fields.fields import (
    EncryptedCharField as _BaseEncryptedCharField,
)
from encrypted_model_fields.fields import (
    EncryptedDateField as _BaseEncryptedDateField,
)
from encrypted_model_fields.fields import (
    EncryptedEmailField as _BaseEncryptedEmailField,
)
from encrypted_model_fields.fields import (
    EncryptedTextField as _BaseEncryptedTextField,
)


class _FallbackMixin:
    """
    Gracefully handle legacy plaintext values so we can encrypt them lazily.
    """

    empty_values = (None, "")

    def from_db_value(self, value, expression, connection):  # noqa: D401
        if value in self.empty_values:
            return value
        try:
            return super().from_db_value(value, expression, connection)
        except Exception:  # pragma: no cover - best-effort guard
            return value

    def to_python(self, value):  # noqa: D401
        if value in self.empty_values:
            return value
        try:
            return super().to_python(value)
        except Exception:  # pragma: no cover
            return value


class EncryptedCharField(_FallbackMixin, _BaseEncryptedCharField):
    """CharField variant that tolerates legacy plaintext records."""


class EncryptedTextField(_FallbackMixin, _BaseEncryptedTextField):
    """TextField variant that tolerates legacy plaintext records."""


class EncryptedEmailField(_FallbackMixin, _BaseEncryptedEmailField):
    """EmailField variant with plaintext fallback."""


class EncryptedDateField(_FallbackMixin, _BaseEncryptedDateField):
    """DateField variant with plaintext fallback."""
