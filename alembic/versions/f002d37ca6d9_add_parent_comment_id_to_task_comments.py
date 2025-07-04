"""Add parent_comment_id to task_comments

Revision ID: f002d37ca6d9
Revises: 8621e3388a45
Create Date: 2025-06-02 22:43:04.605225

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "f002d37ca6d9"
down_revision: Union[str, None] = "8621e3388a45"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "task_comments",
        sa.Column(
            "parent_comment_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )
    op.create_foreign_key(
        None, "task_comments", "task_comments", ["parent_comment_id"], ["id"]
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "task_comments", type_="foreignkey")
    op.drop_column("task_comments", "parent_comment_id")
    # ### end Alembic commands ###
