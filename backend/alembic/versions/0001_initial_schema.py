"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("domain"),
    )

    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=False),
        sa.Column("last_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email"),
    )

    lead_status = postgresql.ENUM(
        "NEW", "QUALIFYING", "QUALIFIED", "DISQUALIFIED", name="lead_status", create_type=False
    )
    lead_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("status", lead_status, nullable=False, server_default="NEW"),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    deal_stage = postgresql.ENUM(
        "OPEN", "PROPOSAL_SENT", "NEGOTIATION", "WON", "LOST", name="deal_stage", create_type=False
    )
    deal_stage.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "deals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("stage", deal_stage, nullable=False, server_default="OPEN"),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("close_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    quote_status = postgresql.ENUM(
        "DRAFT", "SENT", "ACCEPTED", "REJECTED", name="quote_status", create_type=False
    )
    quote_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("discount_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("status", quote_status, nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    conversation_role = postgresql.ENUM(
        "LEAD", "AGENT", "HUMAN_REP", "SYSTEM", name="conversation_role", create_type=False
    )
    conversation_role.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=True),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id", ondelete="CASCADE"), nullable=True),
        sa.Column("role", conversation_role, nullable=False),
        sa.Column("agent_name", sa.String(255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("conversations")
    op.drop_table("quotes")
    op.drop_table("deals")
    op.drop_table("leads")
    op.drop_table("contacts")
    op.drop_table("accounts")

    postgresql.ENUM(name="conversation_role").drop(op.get_bind())
    postgresql.ENUM(name="quote_status").drop(op.get_bind())
    postgresql.ENUM(name="deal_stage").drop(op.get_bind())
    postgresql.ENUM(name="lead_status").drop(op.get_bind())
