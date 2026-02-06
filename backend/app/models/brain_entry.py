"""Brain entry model for Second Brain knowledge storage."""

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Enum as SQLEnum

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.brain_embedding import BrainEmbedding
    from app.models.user import User


class BrainEntryType(str, enum.Enum):
    """Brain entry type enum."""

    MANUAL = "manual"
    CHAT_EXTRACT = "chat_extract"
    URL_IMPORT = "url_import"
    FILE_IMPORT = "file_import"
    VOICE_NOTE = "voice_note"


class EmbeddingStatus(str, enum.Enum):
    """Embedding processing status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BrainEntry(BaseModel):
    """Brain entry model representing a knowledge entry in the Second Brain."""

    __tablename__ = "brain_entries"
    __table_args__ = (
        Index("ix_brain_entries_user_type", "user_id", "entry_type"),
        Index("ix_brain_entries_tags", "tags", postgresql_using="gin"),
        Index(
            "ix_brain_entries_user_created",
            "user_id",
            "created_at",
            postgresql_ops={"created_at": "DESC"},
        ),
        {"comment": "Second Brain knowledge entries"},
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this entry",
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Entry title",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Entry content (full text)",
    )

    entry_type: Mapped[BrainEntryType] = mapped_column(
        SQLEnum(BrainEntryType, name="brain_entry_type", create_type=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        server_default="manual",
        comment="Type: manual, chat_extract, url_import, file_import, voice_note",
    )

    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text),
        nullable=False,
        server_default="{}",
        comment="Tags for categorization",
    )

    source_url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
        comment="Source URL (for imports)",
    )

    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Additional metadata (word_count, language, file info, etc.)",
    )

    embedding_status: Mapped[EmbeddingStatus] = mapped_column(
        SQLEnum(EmbeddingStatus, name="embedding_status", create_type=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        server_default="pending",
        comment="Embedding processing status",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="brain_entries",
        lazy="selectin",
    )

    embeddings: Mapped[list["BrainEmbedding"]] = relationship(
        back_populates="entry",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the brain entry."""
        return f"<BrainEntry(id={self.id}, title={self.title!r}, type={self.entry_type.value})>"
