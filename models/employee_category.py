from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from enum import Enum


class SalaryStructure(str, Enum):
    MONTHLY = "Monthly"
    DAILY = "Daily"
    PIECE_RATE = "Piece-rate"


class EmployeeCategory(Base):
    __tablename__ = "employee_category"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    salary_structure = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to employees
    employees = relationship("Employee", back_populates="category")

    def __repr__(self):
        return f"<EmployeeCategory(id={self.id}, name={self.name}, salary_structure={self.salary_structure})>"
