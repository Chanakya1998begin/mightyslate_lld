"""Generic tool input/output data models."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ToolError(BaseModel):
    """Standardized error payload for tool failures."""

    message: str = Field(..., description="Human-readable error message.")
    code: Optional[str] = Field(default=None, description="Machine-readable error code.")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional structured details providing error context.",
    )


class ToolOutput(BaseModel):
    """Envelope returned by every tool invocation."""

    success: bool = Field(..., description="True when the tool completed successfully.")
    data: Optional[Any] = Field(default=None, description="Resulting payload when success is true.")
    error: Optional[ToolError] = Field(default=None, description="Error details when success is false.")

    @classmethod
    def ok(cls, data: Any = None) -> "ToolOutput":
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> "ToolOutput":
        return cls(success=False, error=ToolError(message=message, code=code, details=details))
