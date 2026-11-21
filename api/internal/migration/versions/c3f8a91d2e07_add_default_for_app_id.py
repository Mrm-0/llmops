"""add missing server defaults for app table

初始迁移（b2938bb40a00）建 app 表时没有写入 server_default，
与 internal/model/app.py 中的模型定义不一致，导致：
  INSERT INTO app (...) 省略 id/updated_at/created_at 时报
  NotNullViolation: null value in column "id" of relation "app"

Revision ID: c3f8a91d2e07
Revises: 194ab2d08417
Create Date: 2026-11-01 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f8a91d2e07'
down_revision = '194ab2d08417'
branch_labels = None
depends_on = None


# 列名 -> (类型, server_default)
_COLUMNS = [
    ('id', sa.UUID(), sa.text('gen_random_uuid()')),
    ('name', sa.String(length=255), sa.text("''::character varying")),
    ('icon', sa.String(length=255), sa.text("''::character varying")),
    ('description', sa.Text(), sa.text("''::text")),
    ('status', sa.String(length=255), sa.text("''::character varying")),
    ('updated_at', sa.DateTime(), sa.text('CURRENT_TIMESTAMP(0)')),
    ('created_at', sa.DateTime(), sa.text('CURRENT_TIMESTAMP(0)')),
]


def upgrade():
    for name, col_type, default in _COLUMNS:
        op.alter_column(
            'app',
            name,
            existing_type=col_type,
            existing_nullable=False,
            server_default=default,
        )


def downgrade():
    for name, col_type, _ in _COLUMNS:
        op.alter_column(
            'app',
            name,
            existing_type=col_type,
            existing_nullable=False,
            server_default=None,
        )
