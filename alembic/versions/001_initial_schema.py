"""Initial schema — all 5 tables.

Revision ID: 001
Revises:
Create Date: 2026-06-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("settings", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_companies")),
        sa.UniqueConstraint("slug", name=op.f("uq_companies_slug")),
    )
    op.create_index(op.f("ix_companies_slug"), "companies", ["slug"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("messenger", sa.String(50), nullable=False),
        sa.Column("messenger_user_id", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("role", sa.String(50), server_default=sa.text("'user'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("company_id", "messenger", "messenger_user_id", name="uq_user_messenger"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_users_company_id")),
    )
    op.create_index(op.f("ix_users_company_id"), "users", ["company_id"])

    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("messenger", sa.String(50), nullable=False),
        sa.Column("messenger_chat_id", sa.String(255), nullable=False),
        sa.Column("previous_response_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), server_default=sa.text("'active'"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversations")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_conversations_company_id")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_conversations_user_id")),
    )
    op.create_index(op.f("ix_conversations_company_id"), "conversations", ["company_id"])
    op.create_index(op.f("ix_conversations_user_id"), "conversations", ["user_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("tool_calls", postgresql.JSONB(), nullable=True),
        sa.Column("tool_call_id", sa.String(255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_messages")),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], name=op.f("fk_messages_conversation_id")),
    )
    op.create_index(op.f("ix_messages_conversation_id"), "messages", ["conversation_id"])

    op.create_table(
        "integrations",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("plugin_name", sa.String(100), nullable=False),
        sa.Column("config", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_integrations")),
        sa.UniqueConstraint("company_id", "plugin_name", name="uq_company_plugin"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_integrations_company_id")),
    )
    op.create_index(op.f("ix_integrations_company_id"), "integrations", ["company_id"])


def downgrade() -> None:
    op.drop_table("integrations")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("users")
    op.drop_table("companies")
