from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.core.constants import GROUP_ADMINISTRATIVE_OFFICER

from .models import User
from .services import email_exists


class UserSerializer(serializers.ModelSerializer):
    """One serializer for create/update/read of users (no extra classes)."""

    password = serializers.CharField(
        write_only=True, min_length=8, allow_blank=False, validators=[validate_password]
    )
    role_id = serializers.PrimaryKeyRelatedField(
        source='role', queryset=Group.objects.all(), required=False, allow_null=True
    )
    role = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'password',
            'first_name',
            'last_name',
            'full_name',
            'role_id',
            'role',
            'status',
            'is_active',
            'is_deleted',
            'deleted_at',
            'date_joined',
        ]
        read_only_fields = ['is_deleted', 'deleted_at', 'date_joined']

    def get_fields(self):
        fields = super().get_fields()
        if self.instance is None:
            fields['email'].required = True
            fields['password'].required = True
        else:
            fields['email'].read_only = True
            fields['password'].required = False
        return fields

    def get_role(self, obj):
        role = getattr(obj, 'role', None)
        return role.name if role else None

    def get_full_name(self, obj):
        return obj.get_full_name()

    def validate_email(self, value):
        if email_exists(value):
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            email=validated_data.pop('email'), password=password, **validated_data
        )
        return user

    def update(self, instance, validated_data):
        request = self.context.get('request')
        actor = getattr(request, 'user', None)
        can_manage_role = actor and (
            actor.is_superuser or actor.groups.filter(name=GROUP_ADMINISTRATIVE_OFFICER).exists()
        )
        if 'role' in validated_data and not can_manage_role:
            raise serializers.ValidationError({'role_id': 'Only superusers can change roles.'})
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
