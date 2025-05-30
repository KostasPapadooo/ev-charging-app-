class TomTomAPIException(Exception):
    """Base exception for TomTom API errors"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

class TomTomRateLimitException(TomTomAPIException):
    """Raised when TomTom API rate limit is exceeded"""
    pass

class TomTomAuthenticationException(TomTomAPIException):
    """Raised when TomTom API authentication fails"""
    pass

class TomTomServiceUnavailableException(TomTomAPIException):
    """Raised when TomTom API is temporarily unavailable"""
    pass 