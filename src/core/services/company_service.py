"""Company service — CRUD operations for tenants."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.company import Company


class CompanyService:
    """Service for managing companies (tenants)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, name: str, slug: str, settings: dict | None = None
    ) -> Company:
        """Create a new company."""
        company = Company(name=name, slug=slug, settings=settings or {})
        self.session.add(company)
        await self.session.flush()
        return company

    async def get_by_id(self, company_id: uuid.UUID) -> Company | None:
        """Get company by ID."""
        result = await self.session.execute(
            select(Company).where(Company.id == company_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Company | None:
        """Get company by unique slug."""
        result = await self.session.execute(
            select(Company).where(Company.slug == slug)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Company]:
        """Return all active companies."""
        result = await self.session.execute(
            select(Company).where(Company.is_active == True)
        )
        return list(result.scalars().all())

    async def update_settings(
        self, company_id: uuid.UUID, settings: dict
    ) -> Company:
        """Update company settings (JSONB merge)."""
        company = await self.get_by_id(company_id)
        if company is None:
            raise ValueError(f"Company {company_id} not found")
        company.settings = {**company.settings, **settings}
        await self.session.flush()
        return company

    async def deactivate(self, company_id: uuid.UUID) -> None:
        """Deactivate a company."""
        company = await self.get_by_id(company_id)
        if company is None:
            raise ValueError(f"Company {company_id} not found")
        company.is_active = False
        await self.session.flush()
