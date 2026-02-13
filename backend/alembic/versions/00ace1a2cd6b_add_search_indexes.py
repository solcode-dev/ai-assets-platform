"""add_search_indexes

Revision ID: 00ace1a2cd6b
Revises: 42213168588e
Create Date: 2026-02-08 02:57:42.823905

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '00ace1a2cd6b'
down_revision: Union[str, None] = '42213168588e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. HNSW Index for Vector Search (Cosine Distance 가속)
    # pgvector 0.5.0+ 에서 지원하는 고성능 인덱스 알고리즘
    op.execute(
        "CREATE INDEX idx_assets_embedding_kure_hnsw ON assets "
        "USING hnsw (embedding_kure vector_cosine_ops)"
    )
    
    # 2. GIN Index for Keyword Search (한국어 Simple FTS 가속)
    # prompt와 search_document를 결합한 가상 컬럼에 대한 GIN 인덱스 생성
    op.execute(
        "CREATE INDEX idx_assets_search_document_gin ON assets "
        "USING gin (to_tsvector('simple', prompt || ' ' || coalesce(search_document, '')))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_assets_embedding_kure_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_assets_search_document_gin")
