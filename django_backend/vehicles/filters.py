import django_filters
from .models import Vehicle


class VehicleFilter(django_filters.FilterSet):
    office_id = django_filters.NumberFilter(field_name="office_id")
    status = django_filters.CharFilter(field_name="status")
    vehicle_type = django_filters.CharFilter(field_name="vehicle_type")
    available_from = django_filters.DateTimeFilter(method="filter_noop")
    available_to = django_filters.DateTimeFilter(method="filter_noop")

    class Meta:
        model = Vehicle
        fields = ["office_id", "status", "vehicle_type"]

    def filter_noop(self, queryset, name, value):
        # Availability filtering is applied in the view using the raw params.
        return queryset
