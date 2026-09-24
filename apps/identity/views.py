from django.contrib.auth.models import Group
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.rbac import ALL_ROLE_GROUPS

from .permissions import CanManageOrOwnUser, CanManageUsers, CanViewOrSelfUser, CanViewUsers
from .serializers import UserSerializer
from .services import delete_user, get_active_users


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD for users.

    Endpoints:
        GET    /api/users/       -> List users (paginated, searchable)
        POST   /api/users/       -> Create user (admin/officer only)
        GET    /api/users/{id}/  -> Retrieve user
        PATCH  /api/users/{id}/  -> Partial update (owner/superuser)
        DELETE /api/users/{id}/  -> Soft delete (admin/officer only)
        GET    /api/users/me/    -> Current user profile
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    search_fields = ['email', 'first_name', 'last_name', 'role__name', 'status']
    ordering_fields = ['email', 'first_name', 'last_name', 'status', 'date_joined']

    def get_queryset(self):
        return get_active_users()

    def get_permissions(self):
        if self.action == 'me' or self.action == 'roles':
            return [IsAuthenticated()]
        if self.action in ('create', 'destroy'):
            return [IsAuthenticated(), CanManageUsers()]
        if self.action in ('update', 'partial_update'):
            return [IsAuthenticated(), CanManageOrOwnUser()]
        if self.action == 'list':
            return [IsAuthenticated(), CanViewUsers()]
        return [IsAuthenticated(), CanViewOrSelfUser()]

    def perform_destroy(self, instance):
        delete_user(instance)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(
            request.user, context={**self.get_serializer_context(), 'include_capabilities': True}
        )
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def roles(self, request):
        """Available RBAC roles for assignment (id + name)."""
        groups = Group.objects.filter(name__in=ALL_ROLE_GROUPS).order_by('name')
        return Response([{'id': group.pk, 'name': group.name} for group in groups])
