class BadAPIResponseCode(Exception):
    pass

class APIRequestProcessingError(Exception):
    pass

class APIError(Exception):
    pass

class BadAPIResponseFormat(Exception):
    pass

class UncknownError(Exception):
    pass