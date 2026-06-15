from typing import Any


class DomainError(Exception):
    def __init__(self, message: str, code: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}


class NotFoundError(DomainError):
    def __init__(self, resource: str, identifier: str | None = None):
        details = {"resource": resource}
        if identifier:
            details["identifier"] = identifier
        super().__init__(f"{resource} not found", "NOT_FOUND", details)


class ValidationError(DomainError):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class AuthenticationError(DomainError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(DomainError):
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class InsufficientFundsError(DomainError):
    def __init__(self, available: int, required: int):
        super().__init__(
            "Insufficient funds",
            "INSUFFICIENT_FUNDS",
            {"available": available, "required": required},
        )


class ConflictError(DomainError):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "CONFLICT", details)


class ExchangeRateError(DomainError):
    def __init__(self, message: str = "Exchange rate unavailable"):
        super().__init__(message, "EXCHANGE_RATE_ERROR")


class RateLimitError(DomainError):
    def __init__(self, message: str = "Too many requests"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")
