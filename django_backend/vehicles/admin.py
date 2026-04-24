from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["id", "make", "model", "year", "plate_number", "vehicle_type", "status", "daily_rate", "office"]
    list_filter = ["status", "vehicle_type", "office"]
    search_fields = ["make", "model", "plate_number"]
    ordering = ["make", "model"]
