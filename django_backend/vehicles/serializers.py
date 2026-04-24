from rest_framework import serializers
from offices.models import Office
from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    office_id = serializers.PrimaryKeyRelatedField(
        queryset=Office.objects.all(), source="office"
    )

    class Meta:
        model = Vehicle
        fields = [
            "id", "make", "model", "year", "plate_number",
            "vehicle_type", "status", "daily_rate", "office_id",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_plate_number(self, value):
        qs = Vehicle.objects.filter(plate_number=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                f"A vehicle with plate number '{value}' already exists."
            )
        return value
