from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import RentalStatus


class Rental(Base):
    __tablename__ = "rentals"
    __table_args__ = (
        Index("ix_rentals_vehicle_id", "vehicle_id"),
        Index("ix_rentals_employee_id", "employee_id"),
        Index("ix_rentals_status", "status"),
        # Common query: find active rentals for a specific vehicle
        Index("ix_rentals_vehicle_status", "vehicle_id", "status"),
        # Common query: find active rentals for a specific employee
        Index("ix_rentals_employee_status", "employee_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[RentalStatus] = mapped_column(
        SAEnum(RentalStatus), nullable=False, default=RentalStatus.active
    )

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="rentals")  # noqa: F821
    employee: Mapped["Employee"] = relationship("Employee", back_populates="rentals")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<Rental id={self.id} vehicle_id={self.vehicle_id} "
            f"employee_id={self.employee_id} status={self.status}>"
        )
