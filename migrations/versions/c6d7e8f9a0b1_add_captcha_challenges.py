"""Add expiring single-use citizen captcha challenges."""
from alembic import op
import sqlalchemy as sa

revision = 'c6d7e8f9a0b1'
down_revision = 'b5c6d7e8f9a0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('captcha_challenges',
        sa.Column('id', sa.String(43), primary_key=True),
        sa.Column('answer_digest', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_captcha_challenges_expires_at', 'captcha_challenges', ['expires_at'])


def downgrade():
    op.drop_table('captcha_challenges')
