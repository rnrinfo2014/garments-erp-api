from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from enum import Enum


class EmployeeStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(String(50), primary_key=True, index=True)
    employee_id = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    category_id = Column(String(50), ForeignKey("employee_category.id"), nullable=False, index=True)
    join_date = Column(DateTime(timezone=True), nullable=False)
    phone = Column(String(15), nullable=False)
    address = Column(Text, nullable=False)
    base_rate = Column(Float, nullable=False)  # Individual employee salary/rate
    status = Column(String(10), nullable=False, default=EmployeeStatus.ACTIVE)
    photo_url = Column(String(255), nullable=True)
    acc_code = Column(String(20), nullable=False, unique=True, index=True)  # Reference to accounts table
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship to category
    category = relationship("EmployeeCategory", back_populates="employees")

    def __repr__(self):
        return f"<Employee(id={self.id}, employee_id={self.employee_id}, name={self.name}, base_rate={self.base_rate})>"
