from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from offices.models import Office
from .models import Employee


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["name"] = user.name
        return token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    office_id = serializers.PrimaryKeyRelatedField(
        queryset=Office.objects.all(), source="office", required=False, allow_null=True
    )

    class Meta:
        model = Employee
        fields = ["id", "email", "name", "password", "office_id"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        employee = Employee(**validated_data)
        employee.set_password(password)
        employee.save()
        return employee


class EmployeeSerializer(serializers.ModelSerializer):
    office_id = serializers.PrimaryKeyRelatedField(
        queryset=Office.objects.all(), source="office", required=False, allow_null=True
    )

    class Meta:
        model = Employee
        fields = ["id", "email", "name", "role", "office_id", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["id", "email", "name", "role", "office_id"]
        read_only_fields = ["id", "email", "name", "role", "office_id"]
