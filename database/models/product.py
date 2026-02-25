"""
Product, Category, Variant, Image, FAQ, Tag, Attribute models
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    Numeric, ForeignKey, JSON, Index, UniqueConstraint, Enum
)
from sqlalchemy.orm import relationship
from .base import Base


class ProductCategory(Base):
    __tablename__ = 'product_categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    image = Column(String(255))
    icon = Column(String(255))
    parent_id = Column(Integer, ForeignKey('product_categories.id', ondelete='CASCADE'))
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    meta_title = Column(String(255))
    meta_description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)

    products = relationship('Product', back_populates='category')
    parent = relationship('ProductCategory', remote_side=[id])
    children = relationship('ProductCategory', back_populates='parent',
                            foreign_keys=[parent_id], overlaps='parent')

    __table_args__ = (
        Index('idx_parent_active', 'parent_id', 'is_active', 'order'),
    )


class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Attribute(Base):
    __tablename__ = 'attributes'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    type = Column(Enum('select', 'color', 'text'), default='select')
    order = Column(Integer, default=0)
    is_filterable = Column(Boolean, default=True)
    is_required = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    values = relationship('AttributeValue', back_populates='attribute')

    __table_args__ = (
        Index('idx_filterable', 'is_filterable', 'is_active'),
    )


class AttributeValue(Base):
    __tablename__ = 'attribute_values'

    id = Column(Integer, primary_key=True)
    attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete='CASCADE'), nullable=False)
    value = Column(String(255), nullable=False)
    color_code = Column(String(7))
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attribute = relationship('Attribute', back_populates='values')

    __table_args__ = (
        Index('idx_attribute', 'attribute_id', 'is_active'),
    )


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    short_description = Column(Text)
    description = Column(Text)
    ingredients = Column(Text)
    how_to_use = Column(Text)
    notes = Column(JSON)
    benefits = Column(JSON)
    category_id = Column(Integer, ForeignKey('product_categories.id', ondelete='CASCADE'), nullable=False)
    brand = Column(String(255))
    origin = Column(String(255))
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    avg_rating = Column(Numeric(3, 2), default=0)
    review_count = Column(Integer, default=0)
    meta_title = Column(String(255))
    meta_description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)

    category = relationship('ProductCategory', back_populates='products')
    variants = relationship('ProductVariant', back_populates='product')
    images = relationship('ProductImage', back_populates='product')
    faqs = relationship('ProductFAQ', back_populates='product')
    reviews = relationship('ProductReview', back_populates='product')

    __table_args__ = (
        Index('idx_slug', 'slug'),
        Index('idx_category', 'category_id', 'is_featured', 'is_active'),
        Index('idx_rating', 'avg_rating'),
        Index('idx_created', 'created_at'),
    )


class ProductVariant(Base):
    __tablename__ = 'product_variants'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    sku = Column(String(255), unique=True, nullable=False)
    barcode = Column(String(255), unique=True)
    price = Column(Numeric(15, 2), nullable=False)
    sale_price = Column(Numeric(15, 2))
    stock_quantity = Column(Integer, default=0)
    alert_quantity = Column(Integer, default=10)
    weight = Column(Numeric(8, 2))
    image = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)

    product = relationship('Product', back_populates='variants')
    order_items = relationship('OrderItem', back_populates='variant')
    variant_attributes = relationship('ProductVariantAttribute', back_populates='variant')

    __table_args__ = (
        Index('idx_product_active', 'product_id', 'is_active'),
        Index('idx_sku', 'sku'),
        Index('idx_stock', 'stock_quantity'),
    )


class ProductVariantAttribute(Base):
    __tablename__ = 'product_variant_attributes'

    id = Column(Integer, primary_key=True)
    variant_id = Column(Integer, ForeignKey('product_variants.id', ondelete='CASCADE'), nullable=False)
    attribute_id = Column(Integer, ForeignKey('attributes.id', ondelete='CASCADE'), nullable=False)
    attribute_value_id = Column(Integer, ForeignKey('attribute_values.id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variant = relationship('ProductVariant', back_populates='variant_attributes')

    __table_args__ = (
        UniqueConstraint('variant_id', 'attribute_id', name='unique_variant_attribute'),
        Index('idx_variant', 'variant_id', 'attribute_id'),
        Index('idx_value', 'attribute_value_id'),
    )


class ProductImage(Base):
    __tablename__ = 'product_images'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    variant_id = Column(Integer, ForeignKey('product_variants.id', ondelete='CASCADE'))
    image_path = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship('Product', back_populates='images')

    __table_args__ = (
        Index('idx_product_primary', 'product_id', 'is_primary'),
        Index('idx_variant_img', 'variant_id'),
    )


class ProductFAQ(Base):
    __tablename__ = 'product_faqs'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    question = Column(String(500), nullable=False)
    answer = Column(Text)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship('Product', back_populates='faqs')

    __table_args__ = (
        Index('idx_product_order', 'product_id', 'order'),
    )


class ProductTag(Base):
    """Bảng pivot product ↔ tag"""
    __tablename__ = 'product_tag'

    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
