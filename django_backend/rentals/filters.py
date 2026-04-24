import django_filters
from .models import Rental


class RentalFilter(django_filters.FilterSet):
    employee_id = django_filters.NumberFilter(field_name="employee_id")
    vehicle_id = django_filters.NumberFilter(field_name="vehicle_id")
    status = django_filters.CharFilter(field_name="status")
    start_after = django_filters.DateTimeFilter(field_name="start_time", lookup_expr="gte")
    start_before = django_filters.DateTimeFilter(field_name="start_time", lookup_expr="lte")

    class Meta:
        model = Rental
        fields = ["employee_id", "vehicle_id", "status"]
