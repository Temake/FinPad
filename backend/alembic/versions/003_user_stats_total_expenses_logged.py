"""Align user_stats column name with ORM model.

Revision ID: 003
Revises: 002
Create Date: 2026-04-23
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # If legacy column exists, rename it; otherwise create the new column.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_stats' AND column_name = 'total_logged'
            ) THEN
                ALTER TABLE user_stats RENAME COLUMN total_logged TO total_expenses_logged;
            ELSIF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_stats' AND column_name = 'total_expenses_logged'
            ) THEN
                ALTER TABLE user_stats ADD COLUMN total_expenses_logged INTEGER DEFAULT 0;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # Restore legacy schema name to match older revisions.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'user_stats' AND column_name = 'total_expenses_logged'
            ) THEN
                ALTER TABLE user_stats RENAME COLUMN total_expenses_logged TO total_logged;
            END IF;
        END $$;
        """
    )
