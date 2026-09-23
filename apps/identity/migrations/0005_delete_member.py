from django.db import migrations


class Migration(migrations.Migration):
    """Drop ``Member`` from ``identity``'s state without touching the table.

    The physical table ``identity_member`` is retained; ownership moves to
    ``apps.members`` via its 0001 initial migration (state-only CreateModel).
    """

    dependencies = [('identity', '0004_member_created_at_member_updated_at_and_more')]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[], state_operations=[migrations.DeleteModel(name='Member')]
        )
    ]
