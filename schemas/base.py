from pydantic import BaseModel


class AppBaseModel(BaseModel):
    """Shared config inherited by all schemas that map to ORM objects."""
    model_config = {"from_attributes": True}
