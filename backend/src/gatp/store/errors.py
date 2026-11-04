"""Store exceptions."""


class NotFoundError(LookupError):
    """The requested row does not exist."""


class ValidationError(ValueError):
    """Input rejected by the store (e.g. unknown author or artifact kind)."""
