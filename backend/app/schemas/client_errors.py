"""Error reports the web app and driver app send when something breaks in the browser."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ClientErrorReport(BaseModel):
    level: Literal["error", "warning"] = "error"
    message: str = Field(..., min_length=1, max_length=2000)
    scope: str = Field(default="app", max_length=80, pattern=r"^[A-Za-z0-9_.:/-]+$")
    stack: str | None = Field(default=None, max_length=8000)
    url: str | None = Field(default=None, max_length=2000)
    user_agent: str | None = Field(default=None, max_length=500)
    release: str | None = Field(default=None, max_length=80)
    context: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @field_validator("context")
    @classmethod
    def _small_context(cls, value: dict) -> dict:
        # A handful of short fields is enough to find the screen and record that failed.
        if len(value) > 20:
            raise ValueError("context may hold at most 20 fields")
        for key, item in value.items():
            if len(key) > 50 or (isinstance(item, str) and len(item) > 500):
                raise ValueError("context keys are at most 50 characters and values at most 500")
        return value
