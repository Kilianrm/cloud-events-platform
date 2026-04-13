class ValidationError(Exception):
    def __init__(self, code: str, message: str = None):
        self.code = code
        self.message = message or code
        super().__init__(self.message)


class ErrorCodes:
    MISSING_FIELDS = "MISSING_FIELDS"
    INVALID_EVENT_ID = "INVALID_EVENT_ID"
    INVALID_SOURCE = "INVALID_SOURCE"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    INVALID_PAYLOAD = "INVALID_PAYLOAD"