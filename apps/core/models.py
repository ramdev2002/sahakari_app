from django.db import models
from django.db.models import Q
from django.utils import timezone


def soft_delete_state_constraint():
    """
    CHECK constraint that ties ``is_deleted`` to ``deleted_at``.

    One row state (deleted + timestamp) XOR the other (alive + no timestamp).
    Declared per concrete model because Django does not propagate
    ``Meta.constraints`` from abstract bases to children.
    """
    return models.CheckConstraint(
        condition=(
            Q(is_deleted=False, deleted_at__isnull=True)
            | Q(is_deleted=True, deleted_at__isnull=False)
        ),
        name='%(app_label)s_%(class)s_soft_delete_state',
    )


class TimestampedModel(models.Model):
    """Reusable audit timestamps, stored in UTC (Django USE_TZ=True)."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that exposes soft-delete helpers for rows."""

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)

    def soft_delete(self):
        return self.update(is_deleted=True, deleted_at=timezone.now())


class SoftDeleteManager(models.Manager):
    """Default manager that hides soft-deleted rows."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted_only(self):
        return self.all_with_deleted().dead()


class SoftDeleteModel(models.Model):
    """
    Reusable soft-delete base model.

    - Rows are hidden by default (manager filters is_deleted=False).
    - instance.delete() performs a soft delete.
    - .all_with_deleted() / .deleted_only() include them back.
    - .restore() brings a row back.
    """

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def delete(self, *args, **kwargs):
        self.soft_delete()
