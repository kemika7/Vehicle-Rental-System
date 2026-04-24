from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class Office(Base):
    __tablename__ = "offices"
    __table_args__ = (
        UniqueConstraint("name", "location", name="uq_offices_name_location"),
        Index("ix_offices_name", "name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)

    vehicles: Mapped[list["Vehicle"]] = relationship(  # noqa: F821
        "Vehicle", back_populates="office", cascade="all, delete-orphan"
    )
    employees: Mapped[list["Employee"]] = relationship(  # noqa: F821
        "Employee", back_populates="office", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Office id={self.id} name={self.name!r} location={self.location!r}>"
