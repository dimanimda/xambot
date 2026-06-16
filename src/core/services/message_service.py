"""Message service — create and retrieve conversation messages."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.message import Message


class MessageService:
    """Service for managing messages within conversations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str | None = None,
        tool_calls: list[dict] | None = None,
        tool_call_id: str | None = None,
        metadata: dict | None = None,
    ) -> Message:
        """Create a new message in a conversation."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            metadata_=metadata,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_conversation_history(
        self,
        conversation_id: uuid.UUID,
        limit: int = 20,
    ) -> list[Message]:
        """Get the last N messages of a conversation, ordered by created_at ASC."""
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()  # Return in chronological order
        return messages
