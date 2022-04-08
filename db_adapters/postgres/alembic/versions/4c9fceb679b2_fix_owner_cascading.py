"""Fix owner cascading

Revision ID: 4c9fceb679b2
Revises: 6ff228301586
Create Date: 2021-11-22 22:07:48.011698

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "4c9fceb679b2"
down_revision = "6ff228301586"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("fk_chapter_owner", "chapter", type_="foreignkey")
    op.create_foreign_key("fk_chapter_owner", "chapter", "user", ["owner_id"], ["id"], ondelete="SET NULL")
    op.drop_constraint("fk_manga_owner", "manga", type_="foreignkey")
    op.create_foreign_key("fk_manga_owner", "manga", "user", ["owner_id"], ["id"], ondelete="SET NULL")
    op.drop_constraint("uploadsession_fk_session_owner_fkey", "uploadsession", type_="foreignkey")
    op.alter_column("uploadsession", "fk_session_owner", new_column_name="owner_id")
    op.create_foreign_key("fk_session_owner", "uploadsession", "user", ["owner_id"], ["id"], ondelete="CASCADE")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("fk_session_owner", "uploadsession", type_="foreignkey")
    op.alter_column("uploadsession", "owner_id", new_column_name="fk_session_owner")
    op.create_foreign_key("uploadsession_fk_session_owner_fkey", "uploadsession", "user", ["fk_session_owner"], ["id"])
    op.drop_constraint("fk_manga_owner", "manga", type_="foreignkey")
    op.create_foreign_key("fk_manga_owner", "manga", "user", ["owner_id"], ["id"])
    op.drop_constraint("fk_chapter_owner", "chapter", type_="foreignkey")
    op.create_foreign_key("fk_chapter_owner", "chapter", "user", ["owner_id"], ["id"])
    # ### end Alembic commands ###
