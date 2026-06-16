"""Conversation service — dialog lifecycle management."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.conversation import Conversation


class ConversationService:
    """Service for managing conversations (dialogs)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_active(
        self,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        messenger: str,
        messenger_chat_id: str,
    ) -> Conversation:
        """Find an active conversation or create a new one."""
        result = await self.session.execute(
            select(Conversation).where(
                Conversation.company_id == company_id,
                Conversation.user_id == user_id,
                Conversation.messenger_chat_id == messenger_chat_id,
                Conversation.status == "active",
            )
        )
        conversation = result.scalar_one_or_none()
        if conversation is not None:
            return conversation

        conversation = Conversation(
            company_id=company_id,
            user_id=user_id,
            messenger=messenger,
            messenger_chat_id=messenger_chat_id,
        )
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get_by_id(self, conv_id: uuid.UUID) -> Conversation | None:
        """Get conversation by ID."""
        result = await self.session.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        return result.scalar_one_or_none()

    async def update_previous_response_id(
        self, conv_id: uuid.UUID, response_id: str
    ) -> None:
        """Update the previous_response_id for multi-turn AI conversations."""
        conversation = await self.get_by_id(conv_id)
        if conversation is not None:
            conversation.previous_response_id = response_id
            await self.session.flush()

    async def touch_last_message(self, conv_id: uuid.UUID) -> None:
        """Update last_message_at to now."""
        from datetime import datetime, timezone

        conversation = await self.get_by_id(conv_id)
        if conversation is not None:
            conversation.last_message_at = datetime.now(timezone.utc)
            await self.session.flush()

    async def close_conversation(self, conv_id: uuid.UUID) -> None:
        """Mark conversation as closed."""
        conversation = await self.get_by_id(conv_id)
        if conversation is not None:
            conversation.status = "closed"
            await self.session.flush()
