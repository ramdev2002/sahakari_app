from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import IsOwnerOrSuperUser, IsSuperUserOrAdministrativeOfficer
from .serializers import (
    UserCreateSerializer,
    UserResponseSerializer,
    UserUpdateSerializer,
)
from .services import UserService


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User CRUD operations.

    Endpoints:
        GET    /api/users/       -> List users (paginated, searchable)
        POST   /api/users/       -> Create user (admin/superuser only)
        GET    /api/users/{id}/  -> Retrieve user
        PATCH  /api/users/{id}/  -> Partial update
        DELETE /api/users/{id}/  -> Delete user
        GET    /api/users/me/    -> Current user profile
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserService.get_active_users()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action in ('update', 'partial_update'):
            return UserUpdateSerializer
        return UserResponseSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated(), IsSuperUserOrAdministrativeOfficer()]
        if self.action in ('update', 'partial_update'):
            return [IsAuthenticated(), IsOwnerOrSuperUser()]
        if self.action == 'destroy':
            return [IsAuthenticated(), IsSuperUserOrAdministrativeOfficer()]
        if self.action == 'me':
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output = UserResponseSerializer(user)
        return Response(output.data, status=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output = UserResponseSerializer(user)
        return Response(output.data)

    def perform_destroy(self, instance):
        UserService.delete_user(instance)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserResponseSerializer(request.user)
        return Response(serializer.data)
