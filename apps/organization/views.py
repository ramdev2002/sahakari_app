from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.identity.permissions import IsSuperUserOrAdministrativeOfficer

from .models import Department
from .serializers import BranchSerializer, DepartmentSerializer, OrganizationSerializer
from .services import get_active_branches, get_active_organizations, get_departments_of_branch


class OrganizationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationSerializer
    search_fields = ['name', 'code', 'email']
    ordering_fields = ['name', 'code', 'status']

    def get_queryset(self):
        return get_active_organizations()

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperUserOrAdministrativeOfficer()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        instance.soft_delete()


class BranchViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = BranchSerializer
    search_fields = ['code', 'name', 'organization__name']
    ordering_fields = ['code', 'name', 'status']

    def get_queryset(self):
        return get_active_branches()

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperUserOrAdministrativeOfficer()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        instance.soft_delete()


class DepartmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DepartmentSerializer
    search_fields = ['code', 'name', 'branch__code']
    ordering_fields = ['code', 'name', 'status']

    def get_queryset(self):
        queryset = Department.objects.filter(status='active')
        branch = self.request.query_params.get('branch')
        if branch:
            queryset = get_departments_of_branch(branch)
        return queryset

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsSuperUserOrAdministrativeOfficer()]
        return [IsAuthenticated()]

    def perform_destroy(self, instance):
        instance.soft_delete()
