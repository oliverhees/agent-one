"""Refresh token model."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(BaseModel):
    """Refresh token model for JWT authentication."""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who owns this refresh token",
    )

    token: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
        index=True,
        comment="Refresh token string",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Token expiration timestamp",
    )

    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Has this token been revoked?",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        back_populates="refresh_tokens",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        """String representation of the refresh token."""
        token_preview = self.token[:20] + "..." if len(self.token) > 20 else self.token
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, token={token_preview}, revoked={self.is_revoked})>"
