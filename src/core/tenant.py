"""TenantManager — resolves company (tenant) by slug for multi-tenant isolation."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import CompanyNotFoundError, TenantInactiveError
from src.core.models.company import Company
from src.core.services.company_service import CompanyService


class TenantManager:
    """Resolves company (tenant) by slug.

    Provides tenant-level operations: lookup, activation checks,
    and listing of active companies.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._company_service = CompanyService(db)

    async def get_by_slug(self, slug: str) -> Company:
        """Find active company by its unique slug.

        Args:
            slug: Company slug (from webhook URL path).

        Returns:
            Company ORM instance.

        Raises:
            CompanyNotFoundError: No company with this slug exists.
            TenantInactiveError: Company exists but ``is_active=False``.
        """
        company = await self._company_service.get_by_slug(slug)
        if company is None:
            raise CompanyNotFoundError(
                f"Company with slug '{slug}' not found",
                code="COMPANY_NOT_FOUND",
            )
        if not company.is_active:
            raise TenantInactiveError(
                f"Company '{slug}' is deactivated",
                code="TENANT_INACTIVE",
            )
        return company

    async def list_active(self) -> list[Company]:
        """Return all active companies."""
        return await self._company_service.list_active()
