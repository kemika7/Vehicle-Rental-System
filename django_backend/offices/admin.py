from django.contrib import admin
from .models import Office


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "location", "phone", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "location"]
    ordering = ["name"]
