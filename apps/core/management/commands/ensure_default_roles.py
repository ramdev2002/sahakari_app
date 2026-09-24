from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from apps.core.rbac import ALL_ROLE_GROUPS


class Command(BaseCommand):
    help = 'Create the default RBAC role groups matching the Sahakari role catalogue.'

    def handle(self, *args, **options):
        created = 0
        for name in sorted(ALL_ROLE_GROUPS):
            group, was_created = Group.objects.get_or_create(name=name)
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'Created role group "{name}".'))
        self.stdout.write(
            self.style.SUCCESS(f'Done. {created} role group(s) created, users unaffected.')
        )
