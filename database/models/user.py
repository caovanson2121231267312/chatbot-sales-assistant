"""
User & Role models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base


class Role(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship('User', back_populates='role')


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    email_verified_at = Column(DateTime)
    password = Column(String(255), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    avatar = Column(String(255))
    loyalty_points = Column(Integer, default=0)
    role_id = Column(Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    status = Column(Enum('active', 'inactive', 'banned'), default='active')
    remember_token = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)

    role = relationship('Role', back_populates='users')
    orders = relationship('Order', back_populates='user', foreign_keys='Order.user_id')
    reviews = relationship('ProductReview', back_populates='user')
    conversations = relationship('ChatbotConversation', back_populates='user')

    __table_args__ = (
        Index('idx_email', 'email'),
        Index('idx_status', 'status'),
    )
