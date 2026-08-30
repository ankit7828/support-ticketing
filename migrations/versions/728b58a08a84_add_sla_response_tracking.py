"""Add SLA response tracking

Revision ID: 728b58a08a84
Revises: a871424fbad6
Create Date: 2026-08-30 15:15:33.183054

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '728b58a08a84'
down_revision = 'a871424fbad6'
branch_labels = None
depends_on = None


def upgrade():

    with op.batch_alter_table('tickets', schema=None) as batch_op:

        batch_op.add_column(
            sa.Column(
                'response_started_at',
                sa.DateTime(timezone=True),
                nullable=True
            )
        )

        batch_op.add_column(
            sa.Column(
                'response_target_minutes',
                sa.Integer(),
                nullable=False,
                server_default='240'
            )
        )

        batch_op.add_column(
            sa.Column(
                'response_paused_at',
                sa.DateTime(timezone=True),
                nullable=True
            )
        )

        batch_op.add_column(
            sa.Column(
                'response_paused_seconds',
                sa.Integer(),
                nullable=False,
                server_default='0'
            )
        )

        batch_op.add_column(
            sa.Column(
                'response_breached',
                sa.Boolean(),
                nullable=False,
                server_default=sa.text('false')
            )
        )


def downgrade():

    with op.batch_alter_table('tickets', schema=None) as batch_op:

        batch_op.drop_column('response_breached')
        batch_op.drop_column('response_paused_seconds')
        batch_op.drop_column('response_paused_at')
        batch_op.drop_column('response_target_minutes')
        batch_op.drop_column('response_started_at')