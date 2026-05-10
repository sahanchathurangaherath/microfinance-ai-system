from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, UserActivityLog


class UserSerializer(serializers.ModelSerializer):# Used for listing and retrieving users.
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'role_display', 'phone', 'branch',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CreateUserSerializer(serializers.ModelSerializer):#Used by admin to create new staff users.
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'branch', 'password', 'confirm_password'
        ]

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user


class UpdateUserSerializer(serializers.ModelSerializer):
   #Used to update user profile or role.
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'phone', 'branch', 'is_active']


class UserActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserActivityLog
        fields = ['id', 'user_name', 'action', 'ip_address', 'timestamp', 'detail']