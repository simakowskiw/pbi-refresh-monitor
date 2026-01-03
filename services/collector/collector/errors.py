from __future__ import annotations


class PowerBIError(Exception):
    pass


class PowerBIAuthError(PowerBIError):
    pass


class PowerBIRetryableError(PowerBIError):
    def __init__(self, message: str, retry_after_sec: float | None = None):
        super().__init__(message)
        self.retry_after_sec = retry_after_sec


class PowerBIRateLimitError(PowerBIRetryableError):
    pass


class PowerBINotFoundError(PowerBIError):
    pass


class PowerBIRequestError(PowerBIError):
    pass
