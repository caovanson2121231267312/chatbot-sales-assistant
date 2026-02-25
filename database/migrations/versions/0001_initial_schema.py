"""Initial schema — tạo toàn bộ bảng

Revision ID: 0001
Revises:
Create Date: 2026-02-24 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── roles ──────────────────────────────────────────────────────────────
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('email_verified_at', sa.DateTime()),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20)),
        sa.Column('address', sa.Text()),
        sa.Column('avatar', sa.String(255)),
        sa.Column('loyalty_points', sa.Integer(), default=0),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.Enum('active', 'inactive', 'banned'), default='active'),
        sa.Column('remember_token', sa.String(100)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('deleted_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_email', 'users', ['email'])
    op.create_index('idx_status', 'users', ['status'])

    # ── product_categories ─────────────────────────────────────────────────
    op.create_table(
        'product_categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text()),
        sa.Column('image', sa.String(255)),
        sa.Column('icon', sa.String(255)),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('product_categories.id', ondelete='CASCADE')),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('meta_title', sa.String(255)),
        sa.Column('meta_description', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('deleted_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_parent_active', 'product_categories', ['parent_id', 'is_active', 'order'])

    # ── tags ───────────────────────────────────────────────────────────────
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # ── attributes ─────────────────────────────────────────────────────────
    op.create_table(
        'attributes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True),
        sa.Column('type', sa.Enum('select', 'color', 'text'), default='select'),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('is_filterable', sa.Boolean(), default=True),
        sa.Column('is_required', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_filterable', 'attributes', ['is_filterable', 'is_active'])

    # ── attribute_values ───────────────────────────────────────────────────
    op.create_table(
        'attribute_values',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('attribute_id', sa.Integer(), sa.ForeignKey('attributes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('value', sa.String(255), nullable=False),
        sa.Column('color_code', sa.String(7)),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_attribute', 'attribute_values', ['attribute_id', 'is_active'])

    # ── coupons ────────────────────────────────────────────────────────────
    op.create_table(
        'coupons',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('type', sa.Enum('percentage', 'fixed', 'free_shipping'), nullable=False),
        sa.Column('value', sa.Numeric(15, 2), default=0),
        sa.Column('max_discount', sa.Numeric(15, 2)),
        sa.Column('min_order_value', sa.Numeric(15, 2), default=0),
        sa.Column('usage_limit', sa.Integer()),
        sa.Column('usage_per_user', sa.Integer(), default=1),
        sa.Column('used_count', sa.Integer(), default=0),
        sa.Column('points_required', sa.Integer(), default=0),
        sa.Column('applicable_to', sa.Enum('all', 'category', 'product', 'variant'), default='all'),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_public', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('deleted_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_code_active', 'coupons', ['code', 'is_active'])
    op.create_index('idx_dates', 'coupons', ['start_date', 'end_date'])

    # ── products ───────────────────────────────────────────────────────────
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), nullable=False, unique=True),
        sa.Column('short_description', sa.Text()),
        sa.Column('description', sa.Text()),
        sa.Column('ingredients', sa.Text()),
        sa.Column('how_to_use', sa.Text()),
        sa.Column('notes', sa.JSON()),
        sa.Column('benefits', sa.JSON()),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('product_categories.id', ondelete='CASCADE'), nullable=False),
        sa.Column('brand', sa.String(255)),
        sa.Column('origin', sa.String(255)),
        sa.Column('is_featured', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('view_count', sa.Integer(), default=0),
        sa.Column('avg_rating', sa.Numeric(3, 2), default=0),
        sa.Column('review_count', sa.Integer(), default=0),
        sa.Column('meta_title', sa.String(255)),
        sa.Column('meta_description', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('deleted_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_slug', 'products', ['slug'])
    op.create_index('idx_category', 'products', ['category_id', 'is_featured', 'is_active'])
    op.create_index('idx_rating', 'products', ['avg_rating'])
    op.create_index('idx_created', 'products', ['created_at'])

    # ── product_variants ───────────────────────────────────────────────────
    op.create_table(
        'product_variants',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sku', sa.String(255), nullable=False, unique=True),
        sa.Column('barcode', sa.String(255), unique=True),
        sa.Column('price', sa.Numeric(15, 2), nullable=False),
        sa.Column('sale_price', sa.Numeric(15, 2)),
        sa.Column('stock_quantity', sa.Integer(), default=0),
        sa.Column('alert_quantity', sa.Integer(), default=10),
        sa.Column('weight', sa.Numeric(8, 2)),
        sa.Column('image', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('deleted_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_product_active', 'product_variants', ['product_id', 'is_active'])
    op.create_index('idx_sku', 'product_variants', ['sku'])
    op.create_index('idx_stock', 'product_variants', ['stock_quantity'])

    # ── product_variant_attributes ─────────────────────────────────────────
    op.create_table(
        'product_variant_attributes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('variant_id', sa.Integer(), sa.ForeignKey('product_variants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attribute_id', sa.Integer(), sa.ForeignKey('attributes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attribute_value_id', sa.Integer(), sa.ForeignKey('attribute_values.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.UniqueConstraint('variant_id', 'attribute_id', name='unique_variant_attribute'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_variant', 'product_variant_attributes', ['variant_id', 'attribute_id'])
    op.create_index('idx_value', 'product_variant_attributes', ['attribute_value_id'])

    # ── product_images ─────────────────────────────────────────────────────
    op.create_table(
        'product_images',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('variant_id', sa.Integer(), sa.ForeignKey('product_variants.id', ondelete='CASCADE')),
        sa.Column('image_path', sa.String(255), nullable=False),
        sa.Column('is_primary', sa.Boolean(), default=False),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_product_primary', 'product_images', ['product_id', 'is_primary'])
    op.create_index('idx_variant_img', 'product_images', ['variant_id'])

    # ── product_faqs ───────────────────────────────────────────────────────
    op.create_table(
        'product_faqs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question', sa.String(500), nullable=False),
        sa.Column('answer', sa.Text()),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_product_order', 'product_faqs', ['product_id', 'order'])

    # ── product_tag (pivot) ────────────────────────────────────────────────
    op.create_table(
        'product_tag',
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # ── orders ─────────────────────────────────────────────────────────────
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_number', sa.String(255), nullable=False, unique=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('coupon_id', sa.Integer(), sa.ForeignKey('coupons.id', ondelete='SET NULL')),
        sa.Column('customer_name', sa.String(255), nullable=False),
        sa.Column('customer_email', sa.String(255), nullable=False),
        sa.Column('customer_phone', sa.String(255), nullable=False),
        sa.Column('shipping_address', sa.Text(), nullable=False),
        sa.Column('province', sa.String(255)),
        sa.Column('district', sa.String(255)),
        sa.Column('ward', sa.String(255)),
        sa.Column('postal_code', sa.String(20)),
        sa.Column('subtotal', sa.Numeric(15, 2), nullable=False),
        sa.Column('discount_amount', sa.Numeric(15, 2), default=0),
        sa.Column('shipping_fee', sa.Numeric(15, 2), default=0),
        sa.Column('tax_amount', sa.Numeric(15, 2), default=0),
        sa.Column('total', sa.Numeric(15, 2), nullable=False),
        sa.Column('points_earned', sa.Integer(), default=0),
        sa.Column('points_used', sa.Integer(), default=0),
        sa.Column('shipping_method', sa.String(255)),
        sa.Column('shipping_carrier', sa.String(255)),
        sa.Column('tracking_number', sa.String(255)),
        sa.Column('estimated_delivery_date', sa.DateTime()),
        sa.Column('actual_delivery_date', sa.DateTime()),
        sa.Column('payment_method', sa.Enum('cod', 'bank_transfer', 'momo', 'vnpay', 'zalopay'), default='cod'),
        sa.Column('payment_status', sa.Enum('pending', 'paid', 'failed', 'refunded', 'partially_refunded'), default='pending'),
        sa.Column('paid_at', sa.DateTime()),
        sa.Column('status', sa.Enum(
            'pending', 'confirmed', 'processing', 'ready_to_ship',
            'shipping', 'delivered', 'completed', 'cancelled',
            'refunding', 'refunded', 'returned',
        ), default='pending'),
        sa.Column('note', sa.Text()),
        sa.Column('admin_note', sa.Text()),
        sa.Column('cancel_reason', sa.Text()),
        sa.Column('cancelled_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('cancelled_at', sa.DateTime()),
        sa.Column('invoice_pdf_path', sa.String(500)),
        sa.Column('invoice_number', sa.String(50)),
        sa.Column('invoice_issued_at', sa.DateTime()),
        sa.Column('invoice_sent_email', sa.Boolean(), default=False),
        sa.Column('source', sa.String(50), default='web'),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('deleted_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_order_number', 'orders', ['order_number'])
    op.create_index('idx_user_status', 'orders', ['user_id', 'status'])
    op.create_index('idx_payment', 'orders', ['payment_status'])
    op.create_index('idx_created', 'orders', ['created_at'])

    # ── order_items ────────────────────────────────────────────────────────
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('variant_id', sa.Integer(), sa.ForeignKey('product_variants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('sku', sa.String(255), nullable=False),
        sa.Column('variant_attributes', sa.JSON()),
        sa.Column('price', sa.Numeric(15, 2), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('discount_amount', sa.Numeric(15, 2), default=0),
        sa.Column('subtotal', sa.Numeric(15, 2), nullable=False),
        sa.Column('status', sa.Enum(
            'pending', 'confirmed', 'processing', 'shipped',
            'delivered', 'cancelled', 'returned', 'refunded',
        ), default='pending'),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_order', 'order_items', ['order_id'])
    op.create_index('idx_variant', 'order_items', ['variant_id'])

    # ── product_reviews ────────────────────────────────────────────────────
    op.create_table(
        'product_reviews',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id', ondelete='CASCADE'), nullable=False),
        sa.Column('variant_id', sa.Integer(), sa.ForeignKey('product_variants.id', ondelete='CASCADE')),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('order_item_id', sa.Integer(), sa.ForeignKey('order_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text()),
        sa.Column('images', sa.JSON()),
        sa.Column('is_verified_purchase', sa.Boolean(), default=True),
        sa.Column('is_approved', sa.Boolean(), default=False),
        sa.Column('helpful_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.UniqueConstraint('user_id', 'order_item_id', name='unique_user_order_item'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_product_approved', 'product_reviews', ['product_id', 'is_approved'])
    op.create_index('idx_variant_approved', 'product_reviews', ['variant_id', 'is_approved'])

    # ── chatbot_conversations ──────────────────────────────────────────────
    op.create_table(
        'chatbot_conversations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('sender_id', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_session', 'chatbot_conversations', ['session_id'])
    op.create_index('idx_sender', 'chatbot_conversations', ['sender_id'])

    # ── chatbot_messages ───────────────────────────────────────────────────
    op.create_table(
        'chatbot_messages',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('chatbot_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_type', sa.Enum('user', 'bot'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(255)),
        sa.Column('confidence', sa.Numeric(5, 4)),
        sa.Column('entities', sa.JSON()),
        sa.Column('created_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_conversation', 'chatbot_messages', ['conversation_id'])
    op.create_index('idx_intent', 'chatbot_messages', ['intent'])

    # ── chatbot_intents ────────────────────────────────────────────────────
    op.create_table(
        'chatbot_intents',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('intent_name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text()),
        sa.Column('category', sa.String(255)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_category', 'chatbot_intents', ['category'])
    op.create_index('idx_usage', 'chatbot_intents', ['usage_count'])

    # ── chatbot_training_examples ──────────────────────────────────────────
    op.create_table(
        'chatbot_training_examples',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('intent_id', sa.Integer(), sa.ForeignKey('chatbot_intents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('example_text', sa.Text(), nullable=False),
        sa.Column('language', sa.String(10), default='vi'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_intent', 'chatbot_training_examples', ['intent_id'])

    # ── chatbot_responses ──────────────────────────────────────────────────
    op.create_table(
        'chatbot_responses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('intent_id', sa.Integer(), sa.ForeignKey('chatbot_intents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('response_text', sa.Text(), nullable=False),
        sa.Column('response_type', sa.Enum('text', 'button', 'image', 'card'), default='text'),
        sa.Column('response_data', sa.JSON()),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_intent_order', 'chatbot_responses', ['intent_id', 'order'])

    # ── chatbot_feedback ───────────────────────────────────────────────────
    op.create_table(
        'chatbot_feedback',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('chatbot_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', sa.Integer(), sa.ForeignKey('chatbot_messages.id', ondelete='CASCADE')),
        sa.Column('rating', sa.Integer()),
        sa.Column('feedback_text', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('idx_conversation_fb', 'chatbot_feedback', ['conversation_id'])
    op.create_index('idx_rating', 'chatbot_feedback', ['rating'])


def downgrade() -> None:
    # Drop theo thứ tự ngược lại (phụ thuộc FK)
    op.drop_table('chatbot_feedback')
    op.drop_table('chatbot_responses')
    op.drop_table('chatbot_training_examples')
    op.drop_table('chatbot_intents')
    op.drop_table('chatbot_messages')
    op.drop_table('chatbot_conversations')
    op.drop_table('product_reviews')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('product_tag')
    op.drop_table('product_faqs')
    op.drop_table('product_images')
    op.drop_table('product_variant_attributes')
    op.drop_table('product_variants')
    op.drop_table('products')
    op.drop_table('coupons')
    op.drop_table('attribute_values')
    op.drop_table('attributes')
    op.drop_table('tags')
    op.drop_table('product_categories')
    op.drop_table('users')
    op.drop_table('roles')
