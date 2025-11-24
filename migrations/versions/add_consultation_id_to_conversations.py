"""add consultation_id to conversations

Revision ID: add_consultation_id_to_conversations
Revises: 
Create Date: 2025-11-24
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_consultation_id_to_conversations'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add nullable consultation_id column and FK to consultations.id
    op.add_column('conversations', sa.Column('consultation_id', sa.Integer(), nullable=True))
    try:
        op.create_foreign_key('fk_conversations_consultation', 'conversations', 'consultations', ['consultation_id'], ['id'])
    except Exception:
        # if the consultations table doesn't exist yet (unlikely) skip FK creation
        pass


def downgrade():
    try:
        op.drop_constraint('fk_conversations_consultation', 'conversations', type_='foreignkey')
    except Exception:
        pass
    op.drop_column('conversations', 'consultation_id')
