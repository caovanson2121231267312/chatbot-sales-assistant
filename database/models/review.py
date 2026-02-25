"""
ProductReview model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, Boolean, ForeignKey, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


class ProductReview(Base):
    __tablename__ = 'product_reviews'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    variant_id = Column(Integer, ForeignKey('product_variants.id', ondelete='CASCADE'))
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    order_item_id = Column(Integer, ForeignKey('order_items.id', ondelete='CASCADE'), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    images = Column(JSON)
    is_verified_purchase = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship('Product', back_populates='reviews')
    user = relationship('User', back_populates='reviews')

    __table_args__ = (
        UniqueConstraint('user_id', 'order_item_id', name='unique_user_order_item'),
        Index('idx_product_approved', 'product_id', 'is_approved'),
        Index('idx_variant_approved', 'variant_id', 'is_approved'),
    )
