"""initial full schema

Revision ID: <REVISION_ID>
Revises:
Create Date: 2025-11-14
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '<REVISION_ID>'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(120), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(120), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('profile_pic', sa.String(255)),
        sa.Column('is_email_verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime())
    )

    op.create_table(
        'babies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime())
    )

    op.create_table(
        'rash_types',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('care_tips', sa.Text())
    )

    op.create_table(
        'skin_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('baby_id', sa.Integer(), sa.ForeignKey('babies.id')),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('predicted_rash_type', sa.String(100), nullable=False),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('image_path', sa.String(255)),
        sa.Column('created_at', sa.DateTime())
    )

    op.create_table(
        'doctor_shares',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('doctor_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('baby_id', sa.Integer(), sa.ForeignKey('babies.id')),

        sa.Column('shared_by_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('permission', sa.String(20), default='view'),
        sa.Column('shared_at', sa.DateTime()),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('active', sa.Boolean(), default=True),
    )

    op.create_table(
        'shared_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('record_id', sa.Integer(), sa.ForeignKey('skin_records.id')),
        sa.Column('doctor_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('shared_at', sa.DateTime()),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('active', sa.Boolean(), default=True)
    )

    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('record_id', sa.Integer(), sa.ForeignKey('skin_records.id')),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('text', sa.Text()),
        sa.Column('created_at', sa.DateTime())
    )

    op.create_table(
        'consultations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('record_id', sa.Integer(), sa.ForeignKey('skin_records.id')),
        sa.Column('doctor_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('status', sa.String(20)),
        sa.Column('requested_at', sa.DateTime())
    )

    op.create_table(
        'access_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('action', sa.String(50)),
        sa.Column('target_type', sa.String(30)),
        sa.Column('target_id', sa.Integer()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(255)),
        sa.Column('created_at', sa.DateTime())
    )

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('message', sa.Text()),
        sa.Column('json_data', sa.JSON()),
        sa.Column('read', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime())
    )


def downgrade():
    op.drop_table('notifications')
    op.drop_table('access_logs')
    op.drop_table('consultations')
    op.drop_table('comments')
    op.drop_table('shared_records')
    op.drop_table('doctor_shares')
    op.drop_table('skin_records')
    op.drop_table('rash_types')
    op.drop_table('babies')
    op.drop_table('users')
