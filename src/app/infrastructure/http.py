class LogEntryNotFoundException(Exception):
    """Custom exception for query not-found in the persistence layer."""

    def __init__(self, message: str):
        super().__init__(message)