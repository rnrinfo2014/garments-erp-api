from sqlalchemy import Column, Integer, String, DateTime, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from decimal import Decimal


class StockLedger(Base):
    __tablename__ = "stock_ledger"
    
    ledger_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    raw_material_id = Column(String(50), ForeignKey("raw_material_master.id"), nullable=False, index=True)
    size_id = Column(String(50), ForeignKey("size_master.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_type = Column(String(50), nullable=False)
    reference_table = Column(String(100), nullable=True)
    reference_id = Column(Integer, nullable=True)
    qty_in = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    qty_out = Column(Numeric(15, 3), default=Decimal("0.000"), nullable=False)
    rate = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    raw_material = relationship("RawMaterialMaster")
    size = relationship("SizeMaster")
    supplier = relationship("Supplier")
    
    @property
    def amount(self):
        """Calculate the amount: (qty_in - qty_out) * rate"""
        net_qty = (self.qty_in or Decimal("0.00")) - (self.qty_out or Decimal("0.00"))
        return net_qty * (self.rate or Decimal("0.00"))
    
    @property
    def net_quantity(self):
        """Calculate net quantity: qty_in - qty_out"""
        return (self.qty_in or Decimal("0.00")) - (self.qty_out or Decimal("0.00"))
    
    def __repr__(self):
        return f"<StockLedger(ledger_id={self.ledger_id}, raw_material_id='{self.raw_material_id}', qty_in={self.qty_in}, qty_out={self.qty_out})>"
