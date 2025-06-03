"""Add parent_comment_id to task_comments

Revision ID: b269f36b93c1
Revises: 6d31a3f35bb0
Create Date: 2025-06-02 22:11:18.893300

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b269f36b93c1"
down_revision: Union[str, None] = "6d31a3f35bb0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "task_comments",
        sa.Column("parent_comment_id", sa.String(length=32), nullable=True),
    )
    op.create_foreign_key(
        "fk_task_comments_parent_comment_id",
        "task_comments",
        "task_comments",
        ["parent_comment_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_task_comments_parent_comment_id", "task_comments", type_="foreignkey"
    )
    op.drop_column("task_comments", "parent_comment_id")
