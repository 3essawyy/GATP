"""Response models for the API. They define the OpenAPI schema the TS client is generated from."""

from typing import Literal

from pydantic import BaseModel


class Health(BaseModel):
    """Liveness information for the API process."""

    status: Literal["ok"]
    app: str
    version: str
