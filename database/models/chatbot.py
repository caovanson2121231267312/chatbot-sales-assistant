"""
Chatbot-specific models: Conversation, Message, Intent, TrainingExample, Response, Feedback
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric, Enum, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from .base import Base


class ChatbotConversation(Base):
    __tablename__ = 'chatbot_conversations'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    session_id = Column(String(255), nullable=False)
    sender_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='conversations')
    messages = relationship('ChatbotMessage', back_populates='conversation')
    feedbacks = relationship('ChatbotFeedback', back_populates='conversation')

    __table_args__ = (
        Index('idx_session', 'session_id'),
        Index('idx_sender', 'sender_id'),
    )


class ChatbotMessage(Base):
    __tablename__ = 'chatbot_messages'

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('chatbot_conversations.id', ondelete='CASCADE'), nullable=False)
    sender_type = Column(Enum('user', 'bot'), nullable=False)
    message = Column(Text, nullable=False)
    intent = Column(String(255))
    confidence = Column(Numeric(5, 4))
    entities = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship('ChatbotConversation', back_populates='messages')

    __table_args__ = (
        Index('idx_conversation', 'conversation_id'),
        Index('idx_intent', 'intent'),
    )


class ChatbotIntent(Base):
    __tablename__ = 'chatbot_intents'

    id = Column(Integer, primary_key=True)
    intent_name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(255))
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    examples = relationship('ChatbotTrainingExample', back_populates='intent')
    responses = relationship('ChatbotResponse', back_populates='intent')

    __table_args__ = (
        Index('idx_category', 'category'),
        Index('idx_usage', 'usage_count'),
    )


class ChatbotTrainingExample(Base):
    __tablename__ = 'chatbot_training_examples'

    id = Column(Integer, primary_key=True)
    intent_id = Column(Integer, ForeignKey('chatbot_intents.id', ondelete='CASCADE'), nullable=False)
    example_text = Column(Text, nullable=False)
    language = Column(String(10), default='vi')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    intent = relationship('ChatbotIntent', back_populates='examples')

    __table_args__ = (
        Index('idx_intent', 'intent_id'),
    )


class ChatbotResponse(Base):
    __tablename__ = 'chatbot_responses'

    id = Column(Integer, primary_key=True)
    intent_id = Column(Integer, ForeignKey('chatbot_intents.id', ondelete='CASCADE'), nullable=False)
    response_text = Column(Text, nullable=False)
    response_type = Column(Enum('text', 'button', 'image', 'card'), default='text')
    response_data = Column(JSON)
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    intent = relationship('ChatbotIntent', back_populates='responses')

    __table_args__ = (
        Index('idx_intent_order', 'intent_id', 'order'),
    )


class ChatbotFeedback(Base):
    __tablename__ = 'chatbot_feedback'

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('chatbot_conversations.id', ondelete='CASCADE'), nullable=False)
    message_id = Column(Integer, ForeignKey('chatbot_messages.id', ondelete='CASCADE'))
    rating = Column(Integer)
    feedback_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship('ChatbotConversation', back_populates='feedbacks')

    __table_args__ = (
        Index('idx_conversation_fb', 'conversation_id'),
        Index('idx_rating', 'rating'),
    )
