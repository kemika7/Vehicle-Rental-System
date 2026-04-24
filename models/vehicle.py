from sqlalchemy import Enum as SAEnum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import VehicleStatus, VehicleType


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        Index("ix_vehicles_office_id", "office_id"),
        Index("ix_vehicles_status", "status"),
        Index("ix_vehicles_office_status", "office_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plate_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    vehicle_type: Mapped[VehicleType] = mapped_column(
        "type", SAEnum(VehicleType), nullable=False
    )
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[VehicleStatus] = mapped_column(
        SAEnum(VehicleStatus), nullable=False, default=VehicleStatus.available
    )
    office_id: Mapped[int] = mapped_column(ForeignKey("offices.id"), nullable=False)

    office: Mapped["Office"] = relationship("Office", back_populates="vehicles")  # noqa: F821
    rentals: Mapped[list["Rental"]] = relationship(  # noqa: F821
        "Rental", back_populates="vehicle", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Vehicle id={self.id} plate={self.plate_number!r} "
            f"type={self.vehicle_type} status={self.status}>"
        )
