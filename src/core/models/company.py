"""Company (tenant) ORM model."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.core.models.conversation import Conversation
    from src.core.models.integration import Integration
    from src.core.models.user import User


class Company(Base, TimestampMixin):
    """Tenant — each company has its own users, conversations, and integrations."""

    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="company", lazy="selectin"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="company", lazy="selectin"
    )
    integrations: Mapped[list["Integration"]] = relationship(
        "Integration", back_populates="company", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Company {self.slug}>"
