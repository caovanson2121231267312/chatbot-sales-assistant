"""
Order & OrderItem models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, Enum, ForeignKey, JSON, Index, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    order_number = Column(String(255), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    coupon_id = Column(Integer, ForeignKey('coupons.id', ondelete='SET NULL'))
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(255), nullable=False)
    shipping_address = Column(Text, nullable=False)
    province = Column(String(255))
    district = Column(String(255))
    ward = Column(String(255))
    postal_code = Column(String(20))
    subtotal = Column(Numeric(15, 2), nullable=False)
    discount_amount = Column(Numeric(15, 2), default=0)
    shipping_fee = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), nullable=False)
    points_earned = Column(Integer, default=0)
    points_used = Column(Integer, default=0)
    shipping_method = Column(String(255))
    shipping_carrier = Column(String(255))
    tracking_number = Column(String(255))
    estimated_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)
    payment_method = Column(
        Enum('cod', 'bank_transfer', 'momo', 'vnpay', 'zalopay'), default='cod'
    )
    payment_status = Column(
        Enum('pending', 'paid', 'failed', 'refunded', 'partially_refunded'), default='pending'
    )
    paid_at = Column(DateTime)
    status = Column(
        Enum(
            'pending', 'confirmed', 'processing', 'ready_to_ship',
            'shipping', 'delivered', 'completed', 'cancelled',
            'refunding', 'refunded', 'returned'
        ),
        default='pending'
    )
    note = Column(Text)
    admin_note = Column(Text)
    cancel_reason = Column(Text)
    cancelled_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    cancelled_at = Column(DateTime)
    invoice_pdf_path = Column(String(500))
    invoice_number = Column(String(50))
    invoice_issued_at = Column(DateTime)
    invoice_sent_email = Column(Boolean, default=False)
    source = Column(String(50), default='web')
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)

    user = relationship('User', foreign_keys=[user_id], back_populates='orders')
    coupon = relationship('Coupon', back_populates='orders')
    items = relationship('OrderItem', back_populates='order')

    __table_args__ = (
        Index('idx_order_number', 'order_number'),
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_payment', 'payment_status'),
        Index('idx_created', 'created_at'),
    )


class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    variant_id = Column(Integer, ForeignKey('product_variants.id', ondelete='CASCADE'), nullable=False)
    product_name = Column(String(255), nullable=False)
    sku = Column(String(255), nullable=False)
    variant_attributes = Column(JSON)
    price = Column(Numeric(15, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    discount_amount = Column(Numeric(15, 2), default=0)
    subtotal = Column(Numeric(15, 2), nullable=False)
    status = Column(
        Enum('pending', 'confirmed', 'processing', 'shipped',
             'delivered', 'cancelled', 'returned', 'refunded'),
        default='pending'
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship('Order', back_populates='items')
    variant = relationship('ProductVariant', back_populates='order_items')

    __table_args__ = (
        Index('idx_order', 'order_id'),
        Index('idx_variant', 'variant_id'),
    )
