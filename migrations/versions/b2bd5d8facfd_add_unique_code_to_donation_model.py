"""Add unique_code to Donation model

Revision ID: b2bd5d8facfd
Revises: df7f71503e8a
Create Date: 2024-12-03 19:41:16.663901

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2bd5d8facfd'
down_revision = 'df7f71503e8a'
branch_labels = None
depends_on = None


# Inside the upgrade function of your migration script
def upgrade():
    # Step 1: Add the unique_code column as nullable (temporary)
    op.add_column('donation', sa.Column('unique_code', sa.String(), nullable=True))

    # Step 2: Update the existing rows with a unique value for unique_code
    # You could either use a fixed value or generate unique codes
    # Here's an example of setting it with a placeholder (e.g., UUID):
    connection = op.get_bind()
    connection.execute("UPDATE donation SET unique_code = 'temp_unique_code'")

    # Step 3: Alter the column to be NOT NULL after updating the records
    op.alter_column('donation', 'unique_code', existing_type=sa.String(), nullable=False)

    # Step 4: Create a unique constraint on the column
    op.create_unique_constraint('uq_donation_unique_code', 'donation', ['unique_code'])


def downgrade():
    op.drop_constraint('uq_donation_unique_code', 'donation', type_='unique')
    op.drop_column('donation', 'unique_code')
    # ### end Alembic commands ###
