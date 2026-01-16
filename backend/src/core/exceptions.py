"""
Custom Exceptions
Application-specific exceptions with error codes and messages.
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details
            }
        }


# =============================================================================
# Authentication Exceptions
# =============================================================================

class AuthenticationError(AppException):
    """Authentication failed."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid login credentials."""

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message=message)


class TokenExpiredError(AuthenticationError):
    """Token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message=message)


class InvalidTokenError(AuthenticationError):
    """Token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message=message)


class OTPError(AppException):
    """OTP-related error."""

    def __init__(
        self,
        message: str,
        code: str = "OTP_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=400,
            details=details
        )


class OTPExpiredError(OTPError):
    """OTP has expired."""

    def __init__(self):
        super().__init__(
            message="OTP has expired",
            code="OTP_EXPIRED"
        )


class OTPInvalidError(OTPError):
    """Invalid OTP."""

    def __init__(self):
        super().__init__(
            message="Invalid OTP",
            code="OTP_INVALID"
        )


class OTPMaxAttemptsError(OTPError):
    """Maximum OTP attempts exceeded."""

    def __init__(self):
        super().__init__(
            message="Maximum OTP verification attempts exceeded",
            code="OTP_MAX_ATTEMPTS"
        )


class OTPCooldownError(OTPError):
    """OTP resend cooldown active."""

    def __init__(self, remaining_seconds: int):
        super().__init__(
            message=f"Please wait {remaining_seconds} seconds before requesting new OTP",
            code="OTP_COOLDOWN",
            details={"retry_after": remaining_seconds}
        )


# =============================================================================
# Authorization Exceptions
# =============================================================================

class AuthorizationError(AppException):
    """Authorization failed."""

    def __init__(
        self,
        message: str = "You don't have permission to perform this action",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
            details=details
        )


class InsufficientPermissionsError(AuthorizationError):
    """User doesn't have required permissions."""

    def __init__(self, required_permission: str = None):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(
            message="Insufficient permissions",
            details=details
        )


# =============================================================================
# Resource Exceptions
# =============================================================================

class NotFoundError(AppException):
    """Resource not found."""

    def __init__(
        self,
        resource: str = "Resource",
        resource_id: str = None
    ):
        details = {"resource": resource}
        if resource_id:
            details["id"] = resource_id
        super().__init__(
            message=f"{resource} not found",
            code="NOT_FOUND",
            status_code=404,
            details=details
        )


class AlreadyExistsError(AppException):
    """Resource already exists."""

    def __init__(
        self,
        resource: str = "Resource",
        field: str = None,
        value: str = None
    ):
        details = {"resource": resource}
        if field:
            details["field"] = field
        if value:
            details["value"] = value
        super().__init__(
            message=f"{resource} already exists",
            code="CONFLICT",
            status_code=409,
            details=details
        )


# =============================================================================
# Validation Exceptions
# =============================================================================

class ValidationError(AppException):
    """Validation error."""

    def __init__(
        self,
        message: str = "Validation failed",
        field: str = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class InvalidPhoneError(ValidationError):
    """Invalid phone number."""

    def __init__(self, phone: str = None):
        super().__init__(
            message="Invalid phone number format",
            field="phone",
            details={"value": phone} if phone else None
        )


class InvalidEmailError(ValidationError):
    """Invalid email address."""

    def __init__(self, email: str = None):
        super().__init__(
            message="Invalid email address format",
            field="email",
            details={"value": email} if email else None
        )


# =============================================================================
# Rate Limiting Exceptions
# =============================================================================

class RateLimitError(AppException):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Too many requests. Please try again later.",
            code="RATE_LIMITED",
            status_code=429,
            details={"retry_after": retry_after}
        )


# =============================================================================
# Business Logic Exceptions
# =============================================================================

class BusinessError(AppException):
    """Business logic error."""

    def __init__(
        self,
        message: str,
        code: str = "BUSINESS_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=400,
            details=details
        )


class MemberNotActiveError(BusinessError):
    """Member is not in active status."""

    def __init__(self, member_id: str = None):
        super().__init__(
            message="Member is not active",
            code="MEMBER_NOT_ACTIVE",
            details={"member_id": member_id} if member_id else None
        )


class MemberAlreadyExistsError(AlreadyExistsError):
    """Member with this phone/email already exists."""

    def __init__(self, field: str = "phone"):
        super().__init__(
            resource="Member",
            field=field
        )


class EventFullError(BusinessError):
    """Event has reached maximum capacity."""

    def __init__(self, event_id: str = None):
        super().__init__(
            message="Event has reached maximum capacity",
            code="EVENT_FULL",
            details={"event_id": event_id} if event_id else None
        )


class EventRegistrationClosedError(BusinessError):
    """Event registration is closed."""

    def __init__(self, event_id: str = None):
        super().__init__(
            message="Event registration is closed",
            code="REGISTRATION_CLOSED",
            details={"event_id": event_id} if event_id else None
        )


class VotingNotOpenError(BusinessError):
    """Voting is not currently open."""

    def __init__(self, election_id: str = None):
        super().__init__(
            message="Voting is not currently open",
            code="VOTING_NOT_OPEN",
            details={"election_id": election_id} if election_id else None
        )


class AlreadyVotedError(BusinessError):
    """User has already voted in this election."""

    def __init__(self, election_id: str = None):
        super().__init__(
            message="You have already voted in this election",
            code="ALREADY_VOTED",
            details={"election_id": election_id} if election_id else None
        )


class NotEligibleToVoteError(BusinessError):
    """User is not eligible to vote in this election."""

    def __init__(self, reason: str = None):
        super().__init__(
            message="You are not eligible to vote in this election",
            code="NOT_ELIGIBLE",
            details={"reason": reason} if reason else None
        )
