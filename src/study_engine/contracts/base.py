"""Base model configuration for domain contracts."""

from pydantic import BaseModel, ConfigDict


class BaseContract(BaseModel):
    """Base Pydantic model for all Study Engine domain contracts."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
    )
