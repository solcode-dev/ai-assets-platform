"""asset type을 대문자로 변경

Revision ID: 002_change_enum_to_uppercase.py
Revises: 001_initial
Create Date: 2026-02-06 12:17:17.003886

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e572cc226b72'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # AssetType 대문화
    op.execute("ALTER TYPE assettypedb RENAME VALUE 'image' TO 'IMAGE'")
    op.execute("ALTER TYPE assettypedb RENAME VALUE 'video' TO 'VIDEO'")
    
    # JobStatus 대문화
    op.execute("ALTER TYPE jobstatus RENAME VALUE 'pending' TO 'PENDING'")
    op.execute("ALTER TYPE jobstatus RENAME VALUE 'processing' TO 'PROCESSING'")
    op.execute("ALTER TYPE jobstatus RENAME VALUE 'completed' TO 'COMPLETED'")
    op.execute("ALTER TYPE jobstatus RENAME VALUE 'failed' TO 'FAILED'")


def downgrade() -> None:
    # AssetType 소문화
    op.execute("ALTER TYPE assettypedb RENAME VALUE 'IMAGE' TO 'image'")
    op.execute("ALTER TYPE assettypedb RENAME VALUE 'VIDEO' TO 'video'")
    
    # JobStatus 소문화
    op.execute("ALTER TYPE jobstatus RENAME VALUE 'PENDING' TO 'pending'")
    op.execute("ALTER TYPE jobstatus RENAME VALUE 'PROCESSING' TO 'processing'")
    op.execute("ALTER TYPE jobstatus RENAME VALUE 'COMPLETED' TO 'completed'")
    op.execute("ALTER TYPE jobstatus RENAME VALUE 'FAILED' TO 'failed'")
