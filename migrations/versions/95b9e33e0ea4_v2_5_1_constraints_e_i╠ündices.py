"""v2.5.1 constraints e índices

Revision ID: 95b9e33e0ea4
Revises: 289c166d4a03
Create Date: 2025-09-09 14:29:28.566675

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '95b9e33e0ea4'
down_revision = '289c166d4a03'
branch_labels = None
depends_on = None


def upgrade():
    # --- features_categoria_diaria ---
    op.create_unique_constraint(
        "uq_fcdiaria_user_fecha_cat",
        "features_categoria_diaria",
        ["usuario_id", "fecha", "categoria"],
    )
    op.create_index(
        "ix_fcdiaria_usuario_fecha",
        "features_categoria_diaria",
        ["usuario_id", "fecha"],
        unique=False,
    )
    op.create_index(
        "ix_fcdiaria_usuario_categoria",
        "features_categoria_diaria",
        ["usuario_id", "categoria"],
        unique=False,
    )
    op.create_index(
        "ix_fcdiaria_fecha",
        "features_categoria_diaria",
        ["fecha"],
        unique=False,
    )

    # --- features_horarias ---
    op.create_unique_constraint(
        "uq_fchorarias_user_fecha_hora_cat",
        "features_horarias",
        ["usuario_id", "fecha", "hora", "categoria"],
    )
    op.create_index(
        "ix_fchorarias_usuario_id",
        "features_horarias",
        ["usuario_id"],
        unique=False,
    )
    op.create_index(
        "ix_fchorarias_fecha",
        "features_horarias",
        ["fecha"],
        unique=False,
    )
    op.create_index(
        "ix_fchorarias_categoria",
        "features_horarias",
        ["categoria"],
        unique=False,
    )

    # --- features_diarias (opcional pero recomendado) ---
    op.create_unique_constraint(
        "uq_fdiarias_user_fecha_cat",
        "features_diarias",
        ["usuario_id", "fecha", "categoria"],
    )
    op.create_index(
        "ix_fdiarias_usuario_id",
        "features_diarias",
        ["usuario_id"],
        unique=False,
    )
    op.create_index(
        "ix_fdiarias_fecha",
        "features_diarias",
        ["fecha"],
        unique=False,
    )
    op.create_index(
        "ix_fdiarias_categoria",
        "features_diarias",
        ["categoria"],
        unique=False,
    )

    # --- dominio_categoria (si manejas dominios por usuario) ---
    # Descomenta si quieres evitar duplicados por usuario/dominio
    # op.create_unique_constraint(
    #     "uq_domcat_usuario_dominio",
    #     "dominio_categoria",
    #     ["usuario_id", "dominio"],
    # )

def downgrade():
    # features_diarias
    op.drop_index("ix_fdiarias_categoria", table_name="features_diarias")
    op.drop_index("ix_fdiarias_fecha", table_name="features_diarias")
    op.drop_index("ix_fdiarias_usuario_id", table_name="features_diarias")
    op.drop_constraint("uq_fdiarias_user_fecha_cat", "features_diarias", type_="unique")

    # features_horarias
    op.drop_index("ix_fchorarias_categoria", table_name="features_horarias")
    op.drop_index("ix_fchorarias_fecha", table_name="features_horarias")
    op.drop_index("ix_fchorarias_usuario_id", table_name="features_horarias")
    op.drop_constraint("uq_fchorarias_user_fecha_hora_cat", "features_horarias", type_="unique")

    # features_categoria_diaria
    op.drop_index("ix_fcdiaria_fecha", table_name="features_categoria_diaria")
    op.drop_index("ix_fcdiaria_usuario_categoria", table_name="features_categoria_diaria")
    op.drop_index("ix_fcdiaria_usuario_fecha", table_name="features_categoria_diaria")
    op.drop_constraint("uq_fcdiaria_user_fecha_cat", "features_categoria_diaria", type_="unique")

    # dominio_categoria (si lo creaste arriba)
    # op.drop_constraint("uq_domcat_usuario_dominio", "dominio_categoria", type_="unique")