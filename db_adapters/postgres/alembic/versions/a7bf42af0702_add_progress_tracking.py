"""add progress tracking

Revision ID: a7bf42af0702
Revises: fff9833deb2b
Create Date: 2022-09-06 15:12:39.961032

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a7bf42af0702"
down_revision = "fff9833deb2b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "progresstracking",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.Column("chapter_version", sa.Integer(), nullable=False),
        sa.Column("chapter_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapter.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("progresstracking")
    # ### end Alembic commands ###
