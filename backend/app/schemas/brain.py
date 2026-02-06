"""Brain entry schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class BrainEntryCreate(BaseModel):
    """Schema for creating a new brain entry."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Entry title",
        examples=["Notizen zum Meeting"],
    )

    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Entry content (full text)",
        examples=["Heute im Meeting wurde besprochen, dass..."],
    )

    entry_type: str | None = Field(
        None,
        description="Entry type: manual, chat_extract, url_import, file_import, voice_note",
        examples=["manual"],
    )

    tags: list[str] | None = Field(
        None,
        description="Tags for categorization",
        examples=[["meeting", "arbeit"]],
    )

    source_url: str | None = Field(
        None,
        max_length=2000,
        description="Source URL (for imports)",
        examples=["https://example.com/article"],
    )


class BrainEntryUpdate(BaseModel):
    """Schema for updating an existing brain entry."""

    title: str | None = Field(
        None,
        min_length=1,
        max_length=500,
        description="Entry title",
    )

    content: str | None = Field(
        None,
        min_length=1,
        max_length=50000,
        description="Entry content",
    )

    tags: list[str] | None = Field(
        None,
        description="Tags for categorization",
    )


class BrainEntryResponse(BaseModel):
    """Schema for brain entry response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Entry unique identifier")
    user_id: UUID = Field(..., description="User who owns this entry")
    title: str = Field(..., description="Entry title")
    content: str = Field(..., description="Entry content")
    entry_type: str = Field(..., description="Entry type")
    tags: list[str] = Field(default_factory=list, description="Tags")
    source_url: str | None = Field(None, description="Source URL")
    embedding_status: str = Field(..., description="Embedding processing status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class BrainSearchResult(BaseModel):
    """Schema for brain search result with similarity score."""

    entry: BrainEntryResponse = Field(..., description="The matching brain entry")
    score: float = Field(..., description="Similarity score (0-1)")
    matched_chunks: list[str] = Field(
        default_factory=list,
        description="Matched text chunks",
    )
