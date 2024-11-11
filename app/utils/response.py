from typing import Optional, Union, Dict, Any
from enum import Enum
from fastapi.responses import JSONResponse


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class Response:
    def __init__(
        self,
        status: ResponseStatus = ResponseStatus.SUCCESS,
        status_code: Optional[int] = 200,
        message: Optional[str] = "Operation successful",
        data: Optional[Union[str, dict, None]] = None,
        error: Exception | None = None | str | dict
    ):
        self._status = status
        self._status_code = status_code
        self._message = message
        self._data = data
        if (isinstance(error, Exception)):
            self._error = str(error)
        else:
            self._error = error

    def send(self) -> JSONResponse:
        """Format and return the response"""
        return JSONResponse(
            status_code=self._status_code,
            content={
                "status": self._status,
                "message": self._message,
                "data": self._data,
                "error": self._error
            }
        )

    @classmethod
    def success(
        cls,
        message: str = "Operation successful",
        status_code: int = 200
    ) -> Dict[str, Any]:
        """Static method for successful responses"""
        return cls(
            status=ResponseStatus.SUCCESS,
            status_code=status_code,
            message=message
        ).send()

    @classmethod
    def error(
        cls,
        error: Union[dict, str],
        message: str = "Something went wrong",
        status_code: int = 500
    ) -> Dict[str, Any]:
        """Static method for error responses"""
        return cls(
            status=ResponseStatus.ERROR,
            status_code=status_code,
            message=message,
            error=error
        ).send()

    @classmethod
    def success_with_data(
        cls,
        data: Union[dict, str],
        message: str = "Operation successful",
        status_code: int = 200
    ) -> Dict[str, Any]:
        """Static method for successful responses with data"""
        return cls(
            status=ResponseStatus.SUCCESS,
            status_code=status_code,
            message=message,
            data=data
        ).send()