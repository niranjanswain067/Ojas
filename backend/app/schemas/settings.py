"""
Schemas for runtime settings management.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class SettingsResponse(BaseModel):
    """Current application configuration."""

    model_path: str = Field(description="Path to the GGUF model file")
    n_ctx: int = Field(description="Context window in tokens")
    n_threads: int = Field(description="Number of CPU threads for inference")
    n_batch: int = Field(description="Batch size for prompt processing")
    n_gpu_layers: int = Field(description="Number of layers to offload to GPU")
    max_tokens: int = Field(description="Maximum tokens to generate per call")
    temperature: float = Field(description="Sampling temperature")
    iteration_limit: int = Field(description="Max iterations in fix loop")
    test_timeout: int = Field(description="Test timeout in seconds")
    host: str = Field(description="Server bind host")
    port: int = Field(description="Server bind port")
    log_level: str = Field(description="Application log level")
    theme: str = Field(description="UI theme preference")
    editor_font_size: int = Field(default=14, ge=8, le=32, description="Monaco editor font size in pixels")


class SettingsUpdateRequest(BaseModel):
    """Partial update payload for application settings."""

    model_path: Optional[str] = Field(default=None, description="Path to the GGUF model file")
    n_ctx: Optional[int] = Field(default=None, ge=512, le=131072, description="Context window size")
    n_threads: Optional[int] = Field(default=None, ge=1, le=128, description="Inference threads")
    n_batch: Optional[int] = Field(default=None, ge=1, le=4096, description="Batch size")
    n_gpu_layers: Optional[int] = Field(default=None, ge=0, le=200, description="GPU offload layers")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=32768, description="Max generated tokens")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Temperature")
    iteration_limit: Optional[int] = Field(default=None, ge=1, le=50, description="Fix loop iterations limit")
    test_timeout: Optional[int] = Field(default=None, ge=5, le=600, description="Test execution timeout in seconds")
    host: Optional[str] = Field(default=None, description="Server host")
    port: Optional[int] = Field(default=None, ge=1024, le=65535, description="Server port")
    log_level: Optional[Literal["debug", "info", "warning", "error", "critical"]] = Field(
        default=None, description="Log verbosity level"
    )
    theme: Optional[Literal["light", "dark", "system"]] = Field(
        default=None, description="UI color scheme"
    )
    editor_font_size: Optional[int] = Field(
        default=None, ge=8, le=32, description="Monaco editor font size in pixels"
    )

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1024 <= v <= 65535):
            raise ValueError(f"Port must be between 1024 and 65535, got {v}")
        return v


class SettingsUpdateResponse(BaseModel):
    """Response returned when settings are updated."""

    settings: SettingsResponse
    model_reload_required: bool
    model_reload_status: Literal["not_required", "reloaded", "reloading", "error"]
    message: Optional[str] = None

