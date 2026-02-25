"""
Package entry point — import tất cả models để SQLAlchemy nhận diện metadata
"""
from .base import Base, engine, SessionLocal, get_db
from .user import Role, User


class _DbSession:
    """Compatibility shim cho các action files dùng db_session.get_session()"""
    def get_session(self):
        return SessionLocal()


db_session = _DbSession()

from .coupon import Coupon
from .product import (
    ProductCategory, Tag, Attribute, AttributeValue,
    Product, ProductVariant, ProductVariantAttribute,
    ProductImage, ProductFAQ, ProductTag,
)
from .order import Order, OrderItem
from .review import ProductReview
from .chatbot import (
    ChatbotConversation, ChatbotMessage, ChatbotIntent,
    ChatbotTrainingExample, ChatbotResponse, ChatbotFeedback,
)

__all__ = [
    # base
    'Base', 'engine', 'SessionLocal', 'get_db', 'db_session',
    # user
    'Role', 'User',
    # coupon
    'Coupon',
    # product
    'ProductCategory', 'Tag', 'Attribute', 'AttributeValue',
    'Product', 'ProductVariant', 'ProductVariantAttribute',
    'ProductImage', 'ProductFAQ', 'ProductTag',
    # order
    'Order', 'OrderItem',
    # review
    'ProductReview',
    # chatbot
    'ChatbotConversation', 'ChatbotMessage', 'ChatbotIntent',
    'ChatbotTrainingExample', 'ChatbotResponse', 'ChatbotFeedback',
]
