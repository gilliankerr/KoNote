# Generated manually to merge parallel migration branches

from django.db import migrations


class Migration(migrations.Migration):
    """
    Merge migration to unify:
    - Branch 1: Demo flag (0002_add_is_demo_field → 0003_set_demo_flag)
    - Branch 2: Receptionist access (0002_add_receptionist_visible → 0003_add_receptionist_editable → 0004_consolidate)
    """

    dependencies = [
        ('clients', '0003_set_demo_flag_on_existing_clients'),
        ('clients', '0004_consolidate_receptionist_access'),
    ]

    operations = [
        # No operations needed - this just merges the branches
    ]
