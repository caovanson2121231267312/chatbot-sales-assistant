"""
Coupon model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric, Enum, Index
from sqlalchemy.orm import relationship
from .base import Base


class Coupon(Base):
    __tablename__ = 'coupons'

    id = Column(Integer, primary_key=True)
    code = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(Enum('percentage', 'fixed', 'free_shipping'), nullable=False)
    value = Column(Numeric(15, 2), default=0)
    max_discount = Column(Numeric(15, 2))
    min_order_value = Column(Numeric(15, 2), default=0)
    usage_limit = Column(Integer)
    usage_per_user = Column(Integer, default=1)
    used_count = Column(Integer, default=0)
    points_required = Column(Integer, default=0)
    applicable_to = Column(Enum('all', 'category', 'product', 'variant'), default='all')
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)

    orders = relationship('Order', back_populates='coupon')

    __table_args__ = (
        Index('idx_code_active', 'code', 'is_active'),
        Index('idx_dates', 'start_date', 'end_date'),
    )
