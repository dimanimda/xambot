"""User ORM model."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from src.core.models.company import Company
    from src.core.models.conversation import Conversation


class User(Base, TimestampMixin):
    """A user (employee) belonging to a company, identified by messenger + messenger_user_id."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "messenger", "messenger_user_id", name="uq_user_messenger"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id"), nullable=False, index=True
    )
    messenger: Mapped[str] = mapped_column(String(50), nullable=False)
    messenger_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user")

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="users")
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User {self.messenger}:{self.messenger_user_id}>"
