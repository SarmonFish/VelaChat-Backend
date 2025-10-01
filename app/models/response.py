from pydantic import BaseModel

class APIResponse(BaseModel):
    success: bool
    message: str = ""
    data: dict | list | None = None