from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

CODE_OK = 200
CODE_FAIL = 500


class ApiResponse(BaseModel, Generic[T]):
    code: int
    message: str
    data: Optional[T] = None


def success(data: Any = None, message: str = "ok") -> ApiResponse[Any]:
    return ApiResponse(code=CODE_OK, message=message, data=data)


def fail(message: str) -> ApiResponse[None]:
    return ApiResponse(code=CODE_FAIL, message=message, data=None)
