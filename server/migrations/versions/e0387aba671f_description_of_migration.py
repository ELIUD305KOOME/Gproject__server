"""Description of migration

Revision ID: e0387aba671f
Revises: bb843becb7c0
Create Date: 2024-07-09 12:24:01.279616

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0387aba671f'
down_revision = 'bb843becb7c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('arrivaltime', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['user.id'], name=op.f('fk_admin_id_user')),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('employee',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('employee_id', sa.Integer(), nullable=True),
    sa.Column('salary', sa.Float(), nullable=True),
    sa.Column('department', sa.String(length=100), nullable=True),
    sa.Column('position', sa.String(length=100), nullable=True),
    sa.Column('arrivaltime', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['user.id'], name=op.f('fk_employee_id_user')),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('employee_id')
    )
    op.create_table('time_entry',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('arrivaltime', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_time_entry_user_id_user')),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('locations')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('firstname', sa.String(length=150), nullable=False))
        batch_op.add_column(sa.Column('lastname', sa.String(length=150), nullable=False))
        batch_op.add_column(sa.Column('gender', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('contacts', sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column('arrivaltime', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('last_login', sa.DateTime(), nullable=True))
        batch_op.drop_column('name')
        batch_op.drop_column('display_photo')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('display_photo', sa.VARCHAR(length=200), nullable=True))
        batch_op.add_column(sa.Column('name', sa.VARCHAR(length=150), nullable=False))
        batch_op.drop_column('last_login')
        batch_op.drop_column('arrivaltime')
        batch_op.drop_column('contacts')
        batch_op.drop_column('gender')
        batch_op.drop_column('lastname')
        batch_op.drop_column('firstname')

    op.create_table('locations',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('country', sa.VARCHAR(length=100), nullable=False),
    sa.Column('county', sa.VARCHAR(length=100), nullable=False),
    sa.Column('town', sa.VARCHAR(length=100), nullable=False),
    sa.Column('postal_code', sa.VARCHAR(length=20), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_locations_user_id_user'),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('time_entry')
    op.drop_table('employee')
    op.drop_table('admin')
    # ### end Alembic commands ###
