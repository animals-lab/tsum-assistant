"""init

Revision ID: 54fb9519ea4e
Revises: 
Create Date: 2025-01-21 19:24:30.785626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '54fb9519ea4e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('brand',
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('name')
    )
    op.create_table('customer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('gender', sa.Enum('MALE', 'FEMALE', name='customergender'), nullable=True),
    sa.Column('age', sa.Integer(), nullable=True),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('style_preferences', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('customer_brand_preference',
    sa.Column('customer_id', sa.Integer(), nullable=False),
    sa.Column('brand_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('preference', sa.Enum('LIKE', 'DISLIKE', name='preferencetype'), nullable=False),
    sa.ForeignKeyConstraint(['brand_name'], ['brand.name'], ),
    sa.ForeignKeyConstraint(['customer_id'], ['customer.id'], ),
    sa.PrimaryKeyConstraint('customer_id', 'brand_name')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('customer_brand_preference')
    op.drop_table('customer')
    op.drop_table('brand')
    # ### end Alembic commands ###
