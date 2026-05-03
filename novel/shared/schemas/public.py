from typing import TypeVar, Generic

from pydantic import BaseModel

T = TypeVar('T')
class APIResponse(BaseModel, Generic[T]):
    code: int
    data: T | None = None
    message: str

    @classmethod
    def success(cls, code: int = 200,data: T | None = None, message:str = "success") -> APIResponse[T]:
        return APIResponse(code=code, data=data,message=message)

    @classmethod
    def failure(cls, code: int = 400, data: T | None = None,message:str = "failure") -> APIResponse[T]:
        return APIResponse(code=code, data=data,message=message)