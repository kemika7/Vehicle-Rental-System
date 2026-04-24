from rest_framework import serializers
from employees.models import Employee
from employees.serializers import EmployeeSerializer
from vehicles.models import Vehicle
from vehicles.serializers import VehicleSerializer
from .models import Rental


class RentalCreateSerializer(serializers.ModelSerializer):
    vehicle_id = serializers.PrimaryKeyRelatedField(queryset=Vehicle.objects.all(), source="vehicle")
    employee_id = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all(), source="employee")

    class Meta:
        model = Rental
        fields = ["id", "vehicle_id", "employee_id", "start_time", "end_time", "status"]
        read_only_fields = ["id", "status"]

    def validate(self, data):
        vehicle = data["vehicle"]
        start = data["start_time"]
        end = data.get("end_time")
        instance = self.instance  # None on create

        if end is not None and end <= start:
            raise serializers.ValidationError({"end_time": "end_time must be after start_time."})

        if vehicle.status == Vehicle.Status.MAINTENANCE:
            raise serializers.ValidationError({"vehicle_id": "Vehicle is under maintenance."})

        employee = data["employee"]
        if vehicle.office_id != employee.office_id:
            raise serializers.ValidationError(
                {"vehicle_id": "Vehicle and employee must belong to the same office."}
            )

        if end is not None:
            overlapping_qs = Rental.objects.filter(
                vehicle=vehicle,
                status__in=[Rental.Status.ACTIVE],
                start_time__lt=end,
                end_time__gt=start,
            )
            if instance:
                overlapping_qs = overlapping_qs.exclude(pk=instance.pk)
            if overlapping_qs.exists():
                raise serializers.ValidationError(
                    {"vehicle_id": "Vehicle is already booked during the requested time window."}
                )

        return data


class RentalUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rental
        fields = ["id", "end_time", "status"]
        read_only_fields = ["id"]

    def validate(self, data):
        instance = self.instance
        new_status = data.get("status", instance.status)
        new_end = data.get("end_time", instance.end_time)
        start = instance.start_time

        terminal = {Rental.Status.COMPLETED, Rental.Status.CANCELLED}
        if instance.status in terminal:
            raise serializers.ValidationError(
                {"status": f"Cannot modify a {instance.status} rental."}
            )

        if new_end is not None and new_end <= start:
            raise serializers.ValidationError({"end_time": "end_time must be after start_time."})

        if new_end is not None and new_end != instance.end_time:
            overlapping_qs = Rental.objects.filter(
                vehicle=instance.vehicle,
                status=Rental.Status.ACTIVE,
                start_time__lt=new_end,
                end_time__gt=start,
            ).exclude(pk=instance.pk)
            if overlapping_qs.exists():
                raise serializers.ValidationError(
                    {"end_time": "The new end time overlaps with another active rental."}
                )

        return data


class RentalDetailSerializer(serializers.ModelSerializer):
    vehicle = VehicleSerializer(read_only=True)
    employee = EmployeeSerializer(read_only=True)

    class Meta:
        model = Rental
        fields = ["id", "vehicle", "employee", "start_time", "end_time", "status", "created_at", "updated_at"]
        read_only_fields = fields
