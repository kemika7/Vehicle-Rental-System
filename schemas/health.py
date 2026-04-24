from pydantic import BaseModel


class HealthResponse(BaseModel):
    model_config = {"from_attributes": True}

    status: str
    version: str
