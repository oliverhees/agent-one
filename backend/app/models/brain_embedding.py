"""Brain embedding model for vector similarity search."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

from datetime import datetime
from uuid import uuid4
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as _PG_UUID

if TYPE_CHECKING:
    from app.models.brain_entry import BrainEntry
    from app.models.user import User

# pgvector column type - import at runtime
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback: define Vector as a passthrough for environments without pgvector
    Vector = None


class BrainEmbedding(Base):
    """Brain embedding model for vector chunks of brain entries.

    Note: This model does NOT extend BaseModel because it doesn't need
    created_at/updated_at timestamps. It only has an id primary key.
    """

    __tablename__ = "brain_embeddings"
    __table_args__ = (
        Index(
            "ix_brain_embeddings_vector",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        {"comment": "Vector embeddings for brain entry chunks (pgvector)"},
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
    )

    entry_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("brain_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Brain entry this embedding belongs to",
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this embedding (denormalized for fast filtering)",
    )

    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Text chunk",
    )

    # Vector column: 384 dimensions (Sentence Transformers)
    embedding = mapped_column(
        Vector(384) if Vector else Text,
        nullable=False,
        comment="Vector embedding (384 dimensions, Sentence Transformers)",
    )

    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Position of chunk in original text",
    )

    # Relationships
    entry: Mapped["BrainEntry"] = relationship(
        back_populates="embeddings",
        lazy="selectin",
    )

    user: Mapped["User"] = relationship(
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the brain embedding."""
        return f"<BrainEmbedding(id={self.id}, entry_id={self.entry_id}, chunk_index={self.chunk_index})>"
