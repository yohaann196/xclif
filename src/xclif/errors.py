class UsageError(Exception):
    """A user-facing CLI invocation error."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint
