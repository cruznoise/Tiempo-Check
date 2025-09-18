"""v2.5.2 crear tabla ml_metrics

Revision ID: afbb1453269b
Revises: 95b9e33e0ea4
Create Date: 2025-09-09 14:47:39.340105

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'afbb1453269b'
down_revision = '95b9e33e0ea4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ml_metrics",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("fecha", sa.Date, nullable=False),
        sa.Column("usuario_id", sa.Integer, nullable=False),
        sa.Column("modelo", sa.String(64), nullable=False),
        sa.Column("categoria", sa.String(64), nullable=False),
        sa.Column("hist_days", sa.Integer, nullable=False),
        sa.Column("rows_train", sa.Integer, nullable=False),
        sa.Column("rows_test", sa.Integer, nullable=False),
        sa.Column("metric_mae", sa.Float),
        sa.Column("metric_rmse", sa.Float),
        sa.Column("baseline", sa.String(32)),
        sa.Column("is_promoted", sa.Boolean, server_default=sa.text("0")),
        sa.Column("artifact_path", sa.String(255)),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index(
        "ix_ml_metrics_user_date_cat",
        "ml_metrics",
        ["usuario_id", "fecha", "categoria"],
        unique=False,
    )

def downgrade():
    op.drop_index("ix_ml_metrics_user_date_cat", table_name="ml_metrics")
    op.drop_table("ml_metrics")