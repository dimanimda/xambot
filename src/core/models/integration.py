"""Integration ORM model — encrypted configuration per company + plugin."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.models.base import Base

if TYPE_CHECKING:
    from src.core.models.company import Company


class Integration(Base):
    """Stores encrypted configuration for a plugin within a company (e.g., Bitrix24, MAX)."""

    __tablename__ = "integrations"
    __table_args__ = (
        UniqueConstraint("company_id", "plugin_name", name="uq_company_plugin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id"), nullable=False, index=True
    )
    plugin_name: Mapped[str] = mapped_column(String(100), nullable=False)
    config: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="integrations")

    def __repr__(self) -> str:
        return f"<Integration {self.plugin_name} [{self.company_id}]>"
