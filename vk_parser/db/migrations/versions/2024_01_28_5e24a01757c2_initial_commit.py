"""Initial commit

Revision ID: 5e24a01757c2
Revises:
Create Date: 2024-01-28 20:03:16.981694

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "5e24a01757c2"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

status = postgresql.ENUM(
    "PENDING", "QUEUED", "PROCESSING", "FAILED", "PROCESSED", "CANCELLED", name="status"
)


def upgrade() -> None:
    op.create_table(
        "parser_request",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("status", status, server_default="PENDING", nullable=False),
        sa.Column("input_data", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "result",
            postgresql.JSON(astext_type=sa.Text()),
            server_default="{ }",
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__parser_request")),
    )
    op.create_table(
        "vk_group",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("parser_request_id", sa.BigInteger(), nullable=False),
        sa.Column("vk_id", sa.BigInteger(), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["parser_request_id"],
            ["parser_request.id"],
            name=op.f("fk__vk_group__parser_request_id__parser_request"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__vk_group")),
    )
    op.create_index(
        op.f("ix__vk_group__parser_request_id"),
        "vk_group",
        ["parser_request_id"],
        unique=False,
    )
    op.create_index(op.f("ix__vk_group__url"), "vk_group", ["url"], unique=False)
    op.create_index(op.f("ix__vk_group__vk_id"), "vk_group", ["vk_id"], unique=False)
    op.create_table(
        "vk_group_post",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("vk_group_id", sa.BigInteger(), nullable=False),
        sa.Column("posted_at", sa.DateTime(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column(
            "user_vk_ids",
            postgresql.ARRAY(sa.BigInteger(), as_tuple=True),
            server_default="{ }",
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["vk_group_id"],
            ["vk_group.id"],
            name=op.f("fk__vk_group_post__vk_group_id__vk_group"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__vk_group_post")),
    )
    op.create_index(
        op.f("ix__vk_group_post__posted_at"),
        "vk_group_post",
        ["posted_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix__vk_group_post__vk_group_id"),
        "vk_group_post",
        ["vk_group_id"],
        unique=False,
    )
    op.create_table(
        "vk_group_user",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("vk_group_id", sa.BigInteger(), nullable=False),
        sa.Column("vk_user_id", sa.BigInteger(), nullable=False),
        sa.Column("raw_data", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("first_name", sa.String(length=1024), nullable=True),
        sa.Column("last_name", sa.String(length=1024), nullable=True),
        sa.Column("last_visit_vk_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["vk_group_id"],
            ["vk_group.id"],
            name=op.f("fk__vk_group_user__vk_group_id__vk_group"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk__vk_group_user")),
    )
    op.create_index(
        op.f("ix__vk_group_user__birth_date"),
        "vk_group_user",
        ["birth_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix__vk_group_user__first_name"),
        "vk_group_user",
        ["first_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix__vk_group_user__last_name"),
        "vk_group_user",
        ["last_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix__vk_group_user__last_name"), table_name="vk_group_user")
    op.drop_index(op.f("ix__vk_group_user__first_name"), table_name="vk_group_user")
    op.drop_index(op.f("ix__vk_group_user__birth_date"), table_name="vk_group_user")
    op.drop_table("vk_group_user")
    op.drop_index(op.f("ix__vk_group_post__vk_group_id"), table_name="vk_group_post")
    op.drop_index(op.f("ix__vk_group_post__posted_at"), table_name="vk_group_post")
    op.drop_table("vk_group_post")
    op.drop_index(op.f("ix__vk_group__vk_id"), table_name="vk_group")
    op.drop_index(op.f("ix__vk_group__url"), table_name="vk_group")
    op.drop_index(op.f("ix__vk_group__parser_request_id"), table_name="vk_group")
    op.drop_table("vk_group")
    op.drop_table("parser_request")
    bind = op.get_bind()
    status.drop(bind)
