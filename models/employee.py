from sqlalchemy import Enum as SAEnum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import Role


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        Index("ix_employees_office_id", "office_id"),
        Index("ix_employees_name", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(
        SAEnum(Role), nullable=False, default=Role.employee
    )
    office_id: Mapped[int] = mapped_column(ForeignKey("offices.id"), nullable=False)

    office: Mapped["Office"] = relationship("Office", back_populates="employees")  # noqa: F821
    rentals: Mapped[list["Rental"]] = relationship(  # noqa: F821
        "Rental", back_populates="employee", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Employee id={self.id} name={self.name!r} role={self.role}>"
