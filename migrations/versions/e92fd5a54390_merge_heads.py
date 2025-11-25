"""merge heads

Revision ID: e92fd5a54390
Revises: add_consultation_id_to_conversations, e3a4242b2b8d
Create Date: 2025-11-25 11:40:12.922903

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e92fd5a54390'
down_revision = ('add_consultation_id_to_conversations', 'e3a4242b2b8d')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
