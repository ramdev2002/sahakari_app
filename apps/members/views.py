from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import CanManageMembers, CanViewMembers
from apps.core.rbac import VIEW_MEMBERS, VIEW_OWN_MEMBERS, has_capability

from .serializers import MemberSerializer
from .services import delete_member, get_active_members


class MemberViewSet(viewsets.ModelViewSet):
    """
    CRUD for cooperative members.

    Endpoints:
        GET    /api/members/       -> List members (role-scoped, paginated, searchable)
        POST   /api/members/       -> Create member (admin/officer only)
        GET    /api/members/{id}/  -> Retrieve member
        PATCH  /api/members/{id}/  -> Update member (admin/officer only)
        DELETE /api/members/{id}/  -> Soft delete (admin/officer only)
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MemberSerializer
    search_fields = ['member_no', 'first_name', 'last_name', 'phone', 'status', 'user__email']
    ordering_fields = ['member_no', 'first_name', 'last_name', 'join_date', 'status']

    def get_queryset(self):
        queryset = get_active_members()
        user = self.request.user
        if (
            user.is_authenticated
            and not user.is_superuser
            and has_capability(user, VIEW_OWN_MEMBERS)
            and not has_capability(user, VIEW_MEMBERS)
        ):
            return queryset.filter(user=user)
        return queryset

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), CanManageMembers()]
        return [IsAuthenticated(), CanViewMembers()]

    def perform_destroy(self, instance):
        delete_member(instance)
