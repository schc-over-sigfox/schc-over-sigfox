class SCHCError(Exception):
    """Base class for other exceptions"""
    def __init__(self, message=''):
        Exception.__init__(self, message)
        self.message = message


class LengthMismatchError(SCHCError):
    """Raised when the value of any SCHC field, object or structure
    doesn't match its expected size."""
    def __init__(self, message=''):
        SCHCError.__init__(self, message)


class SCHCTimeoutError(SCHCError):
    """Raised when any timer (SCHC sender or receiver) expires."""
    def __init__(self):
        SCHCError.__init__(self)


class RuleSelectionError(SCHCError):
    """Raised when a Rule ID cannot be selected
    according to the SCHC Profile."""
    def __init__(self, message=''):
        SCHCError.__init__(self, message)


class SenderAbortError(SCHCError):
    """Raised when a SCHC Sender-Abort message is sent or received."""
    def __init__(self, message=''):
        SCHCError.__init__(self, message)


class ReceiverAbortError(SCHCError):
    """Raised when a SCHC Receiver-Abort message is sent or received."""
    def __init__(self, message=''):
        SCHCError.__init__(self, message)


class BadProfileError(SCHCError):
    """Raised when the behavior of the SCHC Sender or Receiver
    does not match the behavior specified by the profile."""
    def __init__(self, message=''):
        SCHCError.__init__(self, message)


class NetworkDownError(SCHCError):
    """Raised when the network is assumed to be unable to transmit data."""
    def __init__(self, message=''):
        SCHCError.__init__(self, message)
