from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class SalesPerson(Base):
    __tablename__ = "salespersons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    target_amount = Column(Float, default=0)
    is_active = Column(Boolean, default=True)

    products = relationship("Product", back_populates="salesperson")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    salesperson_id = Column(Integer, ForeignKey("salespersons.id"), nullable=False)
    name = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    is_delivered = Column(Boolean, default=False)
    created_date = Column(Date, nullable=False)

    salesperson = relationship("SalesPerson", back_populates="products")
