class SCHCError(Exception):
    """Base class for other exceptions"""
    pass


class LengthMismatchError(SCHCError):
    """Raised when the value of any SCHC field, object or structure
    doesn't match its expected size."""
    pass


class SCHCTimeoutError(SCHCError):
    """Raised when any timer (SCHC sender or receiver) expires."""
    pass


class RuleSelectionError(SCHCError):
    """Raised when a Rule ID cannot be selected
    according to the SCHC Profile."""
    pass


class SenderAbortError(SCHCError):
    """Raised when a SCHC Sender-Abort message is sent or received."""
    pass


class ReceiverAbortError(SCHCError):
    """Raised when a SCHC Receiver-Abort message is sent or received."""
    pass


class BadProfileError(SCHCError):
    """Raised when the behavior of the SCHC Sender or Receiver
    does not match the behavior specified by the profile."""
    pass


class NetworkDownError(SCHCError):
    """Raised when the network is assumed to be unable to transmit data."""
    pass
