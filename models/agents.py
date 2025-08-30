from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from models.user import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(100), nullable=False)
    agent_acc_code = Column(String(20), unique=True, nullable=False, index=True)
    address = Column(String(255), nullable=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=True)
    city = Column(String(100), nullable=True)
    phone = Column(String(15), nullable=True)
    status = Column(String(20), default="Active", nullable=False)  # Active, Inactive, Suspended
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    state = relationship("State", back_populates="agents")
    customers = relationship("Customer", back_populates="agent")
    suppliers = relationship("Supplier", back_populates="agent")
    sales = relationship("Sales", back_populates="agent")

    def __repr__(self):
        return f"<Agent(agent_name='{self.agent_name}', agent_acc_code='{self.agent_acc_code}', status='{self.status}')>"
