"""second migration

Revision ID: d84227791de4
Revises: ccab45594a99
Create Date: 2022-05-24 14:03:31.162575

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d84227791de4"
down_revision = "ccab45594a99"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_constraint(None, 'collaborator', type_='foreignkey')
    # op.create_foreign_key(None, 'collaborator', 'board', ['board_id'], ['id'], ondelete='CASCADE')
    # op.alter_column('tg_user', 'tg_id',
    #                 existing_type=sa.INTEGER(),
    #                 nullable=True)
    with op.batch_alter_table("tg_user") as batch_op:
        batch_op.alter_column("tg_id", existing_type=sa.INTEGER(), nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.alter_column('tg_user', 'tg_id',
    #                 existing_type=sa.INTEGER(),
    #                 nullable=False)
    with op.batch_alter_table("tg_user") as batch_op:
        batch_op.alter_column("tg_id", existing_type=sa.INTEGER(), nullable=True)
    # op.drop_constraint(None, 'collaborator', type_='foreignkey')
    # op.create_foreign_key(None, 'collaborator', 'user', ['board_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###
