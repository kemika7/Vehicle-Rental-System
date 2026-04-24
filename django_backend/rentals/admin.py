from django.contrib import admin
from .models import Rental


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ["id", "vehicle", "employee", "start_time", "end_time", "status", "created_at"]
    list_filter = ["status", "vehicle__office"]
    search_fields = ["vehicle__plate_number", "employee__name", "employee__email"]
    ordering = ["-start_time"]
    raw_id_fields = ["vehicle", "employee"]
