from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4e911c063c96"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) workflow
    op.create_table(
        "workflow",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_workflow_name_version", "workflow", ["name", "version"], unique=True)

    # 2) workflow_state
    op.create_table(
        "workflow_state",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("workflow_id", sa.BigInteger(), sa.ForeignKey("workflow.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_terminal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_workflow_state_workflow_name", "workflow_state", ["workflow_id", "name"], unique=True)

    # 3) workflow_transition
    op.create_table(
        "workflow_transition",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("workflow_id", sa.BigInteger(), sa.ForeignKey("workflow.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_state_id", sa.BigInteger(), sa.ForeignKey("workflow_state.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_state_id", sa.BigInteger(), sa.ForeignKey("workflow_state.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_required", sa.String(length=100), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=True),  # optional label: "Submit", "Approve", etc.
    )
    op.create_index(
        "ix_workflow_transition_unique",
        "workflow_transition",
        ["workflow_id", "from_state_id", "to_state_id", "role_required"],
        unique=True,
    )

    # 4) workflow_instance
    op.create_table(
        "workflow_instance",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("workflow_id", sa.BigInteger(), sa.ForeignKey("workflow.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("current_state_id", sa.BigInteger(), sa.ForeignKey("workflow_state.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_by", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_workflow_instance_workflow_state", "workflow_instance", ["workflow_id", "current_state_id"])
    op.create_index("ix_workflow_instance_created_at", "workflow_instance", ["created_at"])

    # 5) audit_event
    op.create_table(
        "audit_event",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("instance_id", sa.BigInteger(), sa.ForeignKey("workflow_instance.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("actor", sa.String(length=200), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),  # e.g., "transition", "update"
        sa.Column("from_state_id", sa.BigInteger(), sa.ForeignKey("workflow_state.id", ondelete="SET NULL"), nullable=True),
        sa.Column("to_state_id", sa.BigInteger(), sa.ForeignKey("workflow_state.id", ondelete="SET NULL"), nullable=True),
        sa.Column("diff", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("request_id", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_audit_event_instance_ts", "audit_event", ["instance_id", "ts"])


def downgrade() -> None:
    op.drop_index("ix_audit_event_instance_ts", table_name="audit_event")
    op.drop_table("audit_event")

    op.drop_index("ix_workflow_instance_created_at", table_name="workflow_instance")
    op.drop_index("ix_workflow_instance_workflow_state", table_name="workflow_instance")
    op.drop_table("workflow_instance")

    op.drop_index("ix_workflow_transition_unique", table_name="workflow_transition")
    op.drop_table("workflow_transition")

    op.drop_index("ix_workflow_state_workflow_name", table_name="workflow_state")
    op.drop_table("workflow_state")

    op.drop_index("ix_workflow_name_version", table_name="workflow")
    op.drop_table("workflow")
