import enum


class Role(str, enum.Enum):
    admin = "admin"
    employee = "employee"


class VehicleStatus(str, enum.Enum):
    available = "available"
    rented = "rented"
    maintenance = "maintenance"


class VehicleType(str, enum.Enum):
    sedan = "sedan"
    suv = "suv"
    van = "van"
    truck = "truck"
    hatchback = "hatchback"


class RentalStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"
