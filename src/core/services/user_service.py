"""User service — get-or-create for messenger users."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.user import User


class UserService:
    """Service for managing users identified by messenger + messenger_user_id."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(
        self,
        company_id: uuid.UUID,
        messenger: str,
        messenger_user_id: str,
        **kwargs,
    ) -> User:
        """Find an existing user or create a new one.

        Thread-safe via unique constraint on (company_id, messenger, messenger_user_id).
        """
        result = await self.session.execute(
            select(User).where(
                User.company_id == company_id,
                User.messenger == messenger,
                User.messenger_user_id == messenger_user_id,
            )
        )
        user = result.scalar_one_or_none()
        if user is not None:
            # Update optional fields if provided
            for field in ("first_name", "last_name", "username", "phone"):
                if field in kwargs and kwargs[field] is not None:
                    setattr(user, field, kwargs[field])
            await self.session.flush()
            return user

        user = User(
            company_id=company_id,
            messenger=messenger,
            messenger_user_id=messenger_user_id,
            first_name=kwargs.get("first_name"),
            last_name=kwargs.get("last_name"),
            username=kwargs.get("username"),
            phone=kwargs.get("phone"),
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def list_by_company(self, company_id: uuid.UUID) -> list[User]:
        """List all users in a company."""
        result = await self.session.execute(
            select(User).where(User.company_id == company_id)
        )
        return list(result.scalars().all())
