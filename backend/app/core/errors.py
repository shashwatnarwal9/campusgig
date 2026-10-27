"""Domain errors.

Services raise these; a single handler in main.py turns them into HTTP responses.
Services never import fastapi.
"""


class DomainError(Exception):
    status_code = 400
    code = "domain_error"
    message = "Request could not be processed."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message


class EmailDomainNotAllowed(DomainError):
    status_code = 400
    code = "email_domain_not_allowed"
    message = "Registration is restricted to @thapar.edu institutional email addresses."


class DuplicateEmail(DomainError):
    status_code = 409
    code = "email_already_registered"
    message = "An account with this email already exists."


class DuplicateRollNo(DomainError):
    status_code = 409
    code = "roll_no_already_registered"
    message = "An account with this roll number already exists."


class InvalidCredentials(DomainError):
    status_code = 401
    code = "invalid_credentials"
    message = "Invalid email or password."


class AccountLocked(DomainError):
    status_code = 429
    code = "account_locked"
    message = "Too many failed login attempts. Try again later."


class NotAuthenticated(DomainError):
    status_code = 401
    code = "not_authenticated"
    message = "Authentication required."


class InvalidQuery(DomainError):
    status_code = 400
    code = "invalid_query"
    message = "Invalid query parameters."


class UnsupportedFileType(DomainError):
    status_code = 415
    code = "unsupported_file_type"
    message = "That file type is not accepted."


class FileTooLarge(DomainError):
    status_code = 413
    code = "file_too_large"
    message = "That file is too large."


class NotGigOwner(DomainError):
    status_code = 403
    code = "not_gig_owner"
    message = "Only the student who posted this gig can do that."


class CannotApplyToOwnGig(DomainError):
    status_code = 400
    code = "cannot_apply_to_own_gig"
    message = "You cannot apply to a gig you posted."


class AlreadyApplied(DomainError):
    status_code = 409
    code = "already_applied"
    message = "You have already applied to this gig."


class GigNotOpen(DomainError):
    status_code = 409
    code = "gig_not_open"
    message = "This gig is no longer accepting applications."


class ApplicationNotFound(DomainError):
    status_code = 404
    code = "application_not_found"
    message = "Application not found."


class InvalidStatusTransition(DomainError):
    status_code = 409
    code = "invalid_status_transition"
    message = "That status change is not allowed."


class GigNotFound(DomainError):
    status_code = 404
    code = "gig_not_found"
    message = "Gig not found."
