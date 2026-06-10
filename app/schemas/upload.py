from pydantic import BaseModel


class UploadImageOut(BaseModel):
    url: str
