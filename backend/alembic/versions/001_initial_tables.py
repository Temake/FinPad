"""Initial tables - users, categories, expenses, gamification.

Revision ID: 001_initial
Revises: 
Create Date: 2026-03-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('phone', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('profile_image_url', sa.Text(), nullable=True),
        sa.Column('whatsapp_id', sa.String(50), unique=True, nullable=True, index=True),
        sa.Column('whatsapp_linked', sa.Boolean(), default=False),
        sa.Column('currency', sa.String(3), default='NGN'),
        sa.Column('notification_enabled', sa.Boolean(), default=True),
        sa.Column('daily_reminder_time', sa.String(5), nullable=True, default='20:00'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('is_custom', sa.Boolean(), default=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    # Expenses table
    op.create_table(
        'expenses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='NGN'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('expense_date', sa.Date(), nullable=False),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id'), nullable=True),
        sa.Column('source', sa.Enum('manual', 'whatsapp', 'bank_sync', name='expense_source'), default='manual'),
        sa.Column('receipt_url', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Badges table (gamification)
    op.create_table(
        'badges',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('criteria_type', sa.String(50), nullable=False),
        sa.Column('criteria_value', sa.Integer(), nullable=False),
    )

    # User badges (many-to-many)
    op.create_table(
        'user_badges',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('badge_id', sa.Integer(), sa.ForeignKey('badges.id'), nullable=False),
        sa.Column('earned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # User stats
    op.create_table(
        'user_stats',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), unique=True, nullable=False),
        sa.Column('current_streak', sa.Integer(), default=0),
        sa.Column('longest_streak', sa.Integer(), default=0),
        sa.Column('total_logged', sa.Integer(), default=0),
        sa.Column('last_log_date', sa.Date(), nullable=True),
        sa.Column('level', sa.String(50), default='Beginner Saver'),
        sa.Column('xp_points', sa.Integer(), default=0),
    )

    # Seed default categories (Nigeria-relevant)
    op.execute("""
        INSERT INTO categories (name, icon, color, is_custom, user_id) VALUES
        ('Food & Groceries', '🍔', '#FF6B6B', false, NULL),
        ('Transport', '🚗', '#4ECDC4', false, NULL),
        ('Airtime & Data', '📱', '#45B7D1', false, NULL),
        ('Bills & Utilities', '💡', '#96CEB4', false, NULL),
        ('Shopping', '🛍️', '#DDA0DD', false, NULL),
        ('Entertainment', '🎬', '#FFD93D', false, NULL),
        ('Health', '💊', '#6BCB77', false, NULL),
        ('Education', '📚', '#4D96FF', false, NULL),
        ('Family & Gifts', '🎁', '#FF8B94', false, NULL),
        ('Savings', '💰', '#2ECC71', false, NULL),
        ('Other', '📦', '#95A5A6', false, NULL);
    """)


def downgrade() -> None:
    op.drop_table('user_stats')
    op.drop_table('user_badges')
    op.drop_table('badges')
    op.drop_table('expenses')
    op.drop_table('categories')
    op.drop_table('users')
    op.execute('DROP TYPE IF EXISTS expense_source')
