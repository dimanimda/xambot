"""Conversation ORM model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base

if TYPE_CHECKING:
    from src.core.models.company import Company
    from src.core.models.message import Message
    from src.core.models.user import User


class Conversation(Base):
    """A conversation (dialog) between a user and the AI bot within a company."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    messenger: Mapped[str] = mapped_column(String(50), nullable=False)
    messenger_chat_id: Mapped[str] = mapped_column(String(255), nullable=False)
    previous_response_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="active")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="conversations")
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        order_by="Message.created_at",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.id} [{self.status}]>"
