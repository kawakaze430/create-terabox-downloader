"""Strict API response models. Upstream URLs, credentials and sessions are intentionally omitted."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Capabilities(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    metadata: bool = True
    preview: bool = False
    download: bool = False
    folders: bool = False
    batch: bool = False
    zip_download: bool = False
    quality_options: bool = False


class SharedFile(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    file_id: str = Field(min_length=1, max_length=256)
    name: str = Field(min_length=1, max_length=512)
    kind: Literal["file", "folder"] = "file"
    size_bytes: int | None = Field(default=None, ge=0)
    mime_type: str | None = Field(default=None, max_length=128)
    qualities: list[str] = Field(default_factory=list, max_length=12)
    preview_available: bool = False
    download_available: bool = False

    @field_validator("name", "file_id")
    @classmethod
    def no_control_characters(cls, value: str) -> str:
        if any(ord(char) < 32 or ord(char) == 127 for char in value):
            raise ValueError("Control characters are not permitted.")
        return value

    @field_validator("name")
    @classmethod
    def basename_only(cls, value: str) -> str:
        if value in (".", "..") or "/" in value or "\\" in value:
            raise ValueError("Use a filename, not a path.")
        return value

    @field_validator("qualities")
    @classmethod
    def valid_qualities(cls, values: list[str]) -> list[str]:
        if len(set(values)) != len(values) or any(
            not v or len(v) > 32 or any(ord(c) < 32 for c in v) for v in values
        ):
            raise ValueError("Invalid or duplicate quality label.")
        return values


class ShareResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    provider: Literal["terabox"] = "terabox"
    files: list[SharedFile] = Field(default_factory=list, max_length=200)
    capabilities: Capabilities = Field(default_factory=Capabilities)
