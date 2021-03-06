"""Add create date to manga[

Revision ID: 5364a1d72c53
Revises: 1f8dc44606d6
Create Date: 2021-08-05 10:44:31.533342

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5364a1d72c53"
down_revision = "1f8dc44606d6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "manga", sa.Column("create_time", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("manga", "create_time")
    # ### end Alembic commands ###
