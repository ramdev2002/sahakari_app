from rest_framework import serializers

from .models import Member


class MemberSerializer(serializers.ModelSerializer):
    """Serializer for cooperative member records (KYC/identity data)."""

    member_no = serializers.CharField(max_length=20, required=False, allow_blank=True)
    user_email = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            'id',
            'member_no',
            'user',
            'user_email',
            'first_name',
            'last_name',
            'full_name',
            'gender',
            'date_of_birth',
            'phone',
            'address',
            'photo',
            'join_date',
            'status',
            'is_deleted',
            'deleted_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['is_deleted', 'deleted_at', 'created_at', 'updated_at']

    def get_user_email(self, obj):
        user = getattr(obj, 'user', None)
        return user.email if user else None

    def get_full_name(self, obj):
        return obj.get_full_name()

    def validate_member_no(self, value):
        value = (value or '').strip()
        if value:
            qs = Member.objects.all_with_deleted().filter(member_no__iexact=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError('A member with this number already exists.')
        return value
