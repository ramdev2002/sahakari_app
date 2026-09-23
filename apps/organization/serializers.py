from rest_framework import serializers

from .models import Branch, Department, Organization


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'code',
            'registration_no',
            'address',
            'email',
            'phone',
            'status',
            'is_deleted',
            'deleted_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['is_deleted', 'deleted_at', 'created_at', 'updated_at']


class BranchSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = Branch
        fields = [
            'id',
            'organization',
            'organization_name',
            'code',
            'name',
            'address',
            'email',
            'phone',
            'status',
            'is_deleted',
            'deleted_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['is_deleted', 'deleted_at', 'created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = [
            'id',
            'branch',
            'name',
            'code',
            'status',
            'is_deleted',
            'deleted_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['is_deleted', 'deleted_at', 'created_at', 'updated_at']
