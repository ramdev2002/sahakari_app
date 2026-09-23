from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import IsOwnerOrSuperUser, IsSuperUserOrAdministrativeOfficer
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
        if self.action in ('create', 'destroy'):
            return [IsAuthenticated(), IsSuperUserOrAdministrativeOfficer()]
        if self.action in ('update', 'partial_update'):
            return [IsAuthenticated(), IsOwnerOrSuperUser()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        delete_user(instance)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
