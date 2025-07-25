"""Initial migration with all models.

Revision ID: 887178a6750d
Revises: 
Create Date: 2025-07-24 10:35:59.072210

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '887178a6750d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=80), nullable=False),
    sa.Column('password_hash', sa.String(length=200), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('application',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('phone_number', sa.String(length=20), nullable=False),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('district', sa.String(length=100), nullable=True),
    sa.Column('position', sa.String(length=100), nullable=False),
    sa.Column('upload_folder', sa.String(length=300), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('submission_date', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('contact_message',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('message_content', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('submission_date', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('admin_reply',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reply_content', sa.Text(), nullable=False),
    sa.Column('reply_date', sa.DateTime(), nullable=True),
    sa.Column('application_id', sa.Integer(), nullable=True),
    sa.Column('message_id', sa.Integer(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['application.id'], ),
    sa.ForeignKeyConstraint(['author_id'], ['admin_user.id'], ),
    sa.ForeignKeyConstraint(['message_id'], ['contact_message.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('admin_reply')
    op.drop_table('contact_message')
    op.drop_table('application')
    op.drop_table('admin_user')
    # ### end Alembic commands ###
