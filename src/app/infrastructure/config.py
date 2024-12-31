class ServiceAccountFileNotFouncError(Exception):
    """Custom exception for missing google service account file."""

    def __init__(self, message: str):
        super().__init__(message)
