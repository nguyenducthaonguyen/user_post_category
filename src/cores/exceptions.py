from fastapi import HTTPException


class APIException(HTTPException):
    def __init__(self, error: str, **kwargs):
        """
        Custom API exception that extends FastAPI's HTTPException.

        :param error: Error message to be included in the response.
        :param kwargs: Additional keyword arguments to pass to HTTPException.
        """
        self.error = error
        super().__init__(**kwargs)



