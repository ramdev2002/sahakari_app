from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User
from .services import UserService


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users. Handles password validation and hashing."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
        help_text='Password must be at least 8 characters.',
    )

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'email', 'password',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_email(self, value):
        if UserService.email_exists(value):
            raise serializers.ValidationError(
                'A user with this email already exists.'
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users. Password changes handled separately."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
        required=False,
        allow_blank=False,
    )

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'email',
            'password', 'is_active',
        ]
        read_only_fields = ['id', 'email']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class UserResponseSerializer(serializers.ModelSerializer):
    """Serializer for user responses. Never exposes password or sensitive fields."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'email', 'is_active',
            'is_deleted', 'deleted_at', 'date_joined',
        ]
        read_only_fields = fields

    def get_full_name(self, obj):
        return obj.get_full_name()
