from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class SalesPerson(Base):
    __tablename__ = "salespersons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    target_amount = Column(Float, default=0)
    is_active = Column(Boolean, default=True)

    products = relationship("Product", back_populates="salesperson")
    monthly_records = relationship("MonthlyRecord", back_populates="salesperson")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    salesperson_id = Column(Integer, ForeignKey("salespersons.id"), nullable=False)
    
    name = Column(String(200), nullable=False)
    years = Column(String(50))
    product_type = Column(String(50))
    grade = Column(String(50))
    param_a = Column(Float, nullable=False)
    production_date = Column(Date)
    expire_date = Column(Date)
    seal_date = Column(Date)
    seal_expire_date = Column(Date)
    contact = Column(String(100))
    address = Column(Text)
    emergency_contact = Column(String(100))
    remark = Column(Text)
    
    is_approved = Column(Boolean, default=True)
    is_delivered = Column(Boolean, default=False)
    created_date = Column(Date, nullable=False)

    salesperson = relationship("SalesPerson", back_populates="products")

    @property
    def amount(self):
        if self.param_a <= 800:
            return 0
        return self.param_a - 800
    
    @property
    def is_valid(self):
        return self.param_a > 800

class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    param_c = Column(Float, default=300)
    param_d = Column(Float, default=500)

class MonthlyRecord(Base):
    __tablename__ = "monthly_records"

    id = Column(Integer, primary_key=True, index=True)
    salesperson_id = Column(Integer, ForeignKey("salespersons.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    
    total_products = Column(Integer, default=0)
    total_amount = Column(Float, default=0)
    delivered_count = Column(Integer, default=0)
    delivered_amount = Column(Float, default=0)
    
    snapshot_date = Column(Date, nullable=False)
    
    salesperson = relationship("SalesPerson", back_populates="monthly_records")
