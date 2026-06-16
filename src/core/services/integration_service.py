"""Integration service — encrypted plugin configuration CRUD."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.integration import Integration
from src.core.security import EncryptionService


class IntegrationService:
    """Service for managing encrypted integration configurations."""

    def __init__(self, session: AsyncSession, encryption: EncryptionService) -> None:
        self.session = session
        self.encryption = encryption

    async def save_config(
        self,
        company_id: uuid.UUID,
        plugin_name: str,
        config: dict,
        enabled: bool = True,
    ) -> Integration:
        """Encrypt config dict and upsert an integration record."""
        encrypted = self.encryption.encrypt(config)

        # Try to find existing
        result = await self.session.execute(
            select(Integration).where(
                Integration.company_id == company_id,
                Integration.plugin_name == plugin_name,
            )
        )
        integration = result.scalar_one_or_none()

        if integration is not None:
            integration.config = encrypted
            integration.enabled = enabled
        else:
            integration = Integration(
                company_id=company_id,
                plugin_name=plugin_name,
                config=encrypted,
                enabled=enabled,
            )
            self.session.add(integration)

        await self.session.flush()
        return integration

    async def get_config(
        self, company_id: uuid.UUID, plugin_name: str
    ) -> dict | None:
        """Decrypt and return config dict. Returns None if not found or disabled."""
        integration = await self._get_integration(company_id, plugin_name)
        if integration is None or not integration.enabled:
            return None
        return self.encryption.decrypt(integration.config)

    async def get_raw_config(
        self, company_id: uuid.UUID, plugin_name: str
    ) -> dict | None:
        """Return decrypted config for an enabled integration, or None."""
        return await self.get_config(company_id, plugin_name)

    async def disable(self, company_id: uuid.UUID, plugin_name: str) -> None:
        """Disable an integration."""
        integration = await self._get_integration(company_id, plugin_name)
        if integration is not None:
            integration.enabled = False
            await self.session.flush()

    async def enable(self, company_id: uuid.UUID, plugin_name: str) -> None:
        """Enable an integration."""
        integration = await self._get_integration(company_id, plugin_name)
        if integration is not None:
            integration.enabled = True
            await self.session.flush()

    async def delete(self, company_id: uuid.UUID, plugin_name: str) -> None:
        """Delete an integration record."""
        integration = await self._get_integration(company_id, plugin_name)
        if integration is not None:
            await self.session.delete(integration)
            await self.session.flush()

    async def _get_integration(
        self, company_id: uuid.UUID, plugin_name: str
    ) -> Integration | None:
        """Internal: fetch integration by company + plugin name."""
        result = await self.session.execute(
            select(Integration).where(
                Integration.company_id == company_id,
                Integration.plugin_name == plugin_name,
            )
        )
        return result.scalar_one_or_none()
