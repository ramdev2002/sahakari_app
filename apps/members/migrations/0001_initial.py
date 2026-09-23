import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """Adopt the ``Member`` model (state only) under ``apps.members``.

    The ``identity_member`` table (and its data / row-level constraints) already
    exist; this migration only moves model ownership. Its physical layout is
    identical to the former ``identity.Member``.
    """

    initial = True

    dependencies = [
        ('identity', '0005_delete_member'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='Member',
                    fields=[
                        (
                            'id',
                            models.UUIDField(
                                default=uuid.uuid4,
                                editable=False,
                                primary_key=True,
                                serialize=False,
                            ),
                        ),
                        ('member_no', models.CharField(blank=True, max_length=20, unique=True)),
                        (
                            'user',
                            models.OneToOneField(
                                blank=True,
                                help_text='Optional login account linked to this member.',
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                related_name='member',
                                to='identity.user',
                            ),
                        ),
                        ('first_name', models.CharField(blank=True, max_length=150)),
                        ('last_name', models.CharField(blank=True, max_length=150)),
                        (
                            'gender',
                            models.CharField(
                                blank=True,
                                choices=[
                                    ('male', 'Male'),
                                    ('female', 'Female'),
                                    ('other', 'Other'),
                                ],
                                max_length=10,
                            ),
                        ),
                        ('date_of_birth', models.DateField(blank=True, null=True)),
                        (
                            'phone',
                            models.CharField(
                                blank=True,
                                help_text='Contact phone number for the member.',
                                max_length=15,
                            ),
                        ),
                        ('address', models.TextField(blank=True)),
                        ('photo', models.ImageField(blank=True, null=True, upload_to='members/')),
                        ('join_date', models.DateField(default=django.utils.timezone.localdate)),
                        (
                            'status',
                            models.CharField(
                                choices=[('active', 'Active'), ('inactive', 'Inactive')],
                                db_index=True,
                                default='active',
                                max_length=20,
                            ),
                        ),
                        ('is_deleted', models.BooleanField(default=False)),
                        ('deleted_at', models.DateTimeField(blank=True, null=True)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        'db_table': 'identity_member',
                        'ordering': ['-join_date'],
                        'constraints': [
                            models.CheckConstraint(
                                condition=models.Q(
                                    ('deleted_at__isnull', True), ('is_deleted', False)
                                )
                                | models.Q(('deleted_at__isnull', False), ('is_deleted', True)),
                                name='members_member_soft_delete_state',
                            )
                        ],
                    },
                )
            ],
        )
    ]
