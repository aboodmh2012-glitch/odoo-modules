class DeliveryUncertain(Exception):
    """The provider may have accepted the request. Do not replay automatically."""


class DeliveryPermanent(Exception):
    """A redacted, user-safe delivery failure."""


class DeliveryTemporary(Exception):
    """Provider explicitly rejected delivery with a retryable response."""
