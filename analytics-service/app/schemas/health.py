from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str = "OK"

class VersionResponse(BaseModel):
    version: str 