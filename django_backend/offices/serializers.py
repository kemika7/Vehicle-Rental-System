from rest_framework import serializers
from .models import Office


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ["id", "name", "location", "phone", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
