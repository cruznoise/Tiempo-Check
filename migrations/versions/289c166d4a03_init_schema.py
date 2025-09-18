"""init schema

Revision ID: 289c166d4a03
Revises: 
Create Date: 2025-09-09 13:59:37.425723

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '289c166d4a03'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Baseline inicial: no modificar el esquema existente
    pass

def downgrade():
    # Baseline inicial: no hay nada que revertir
    pass