"""user add update_time

Revision ID: fff9833deb2b
Revises: 441d31311431
Create Date: 2022-05-30 14:14:06.603604

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fff9833deb2b"
down_revision = "441d31311431"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("user", sa.Column("update_time", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "update_time")
    # ### end Alembic commands ###