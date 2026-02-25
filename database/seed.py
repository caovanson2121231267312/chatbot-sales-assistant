"""
Seed fake data for testing the e-commerce chatbot.
Run: python -m database.seed
"""

import sys, os, random
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.models import (
    Role, User, ProductCategory, Tag, Attribute, AttributeValue,
    Product, ProductVariant, ProductVariantAttribute, ProductImage,
    ProductFAQ, ProductTag, Coupon, Order, OrderItem, ProductReview,
    ChatbotConversation, ChatbotMessage, ChatbotIntent,
    ChatbotTrainingExample, ChatbotResponse, ChatbotFeedback,
    db_session
)
from sqlalchemy import text
import hashlib

# ─── helpers ────────────────────────────────────────────────────────────────

def fake_password(plain="password123"):
    return hashlib.sha256(plain.encode()).hexdigest()

def rand_date(days_back=365):
    return datetime.now() - timedelta(days=random.randint(0, days_back))

def rand_future(days=90):
    return datetime.now() + timedelta(days=random.randint(1, days))

def slugify(t):
    import re, unicodedata
    t = unicodedata.normalize('NFD', t)
    t = t.encode('ascii', 'ignore').decode('ascii')
    t = re.sub(r'[^\w\s-]', '', t.lower())
    return re.sub(r'[-\s]+', '-', t).strip('-')

def rand_phone():
    return f"0{random.choice([3,5,7,8,9])}{random.randint(10000000,99999999)}"

def rand_tracking():
    return f"VN{random.randint(100000000,999999999)}VN"

def rand_ip():
    return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

# ─── seed entry point ────────────────────────────────────────────────────────

def seed():
    session = db_session.get_session()
    try:
        print("Seeding database...")
        _truncate(session)
        roles    = _seed_roles(session)
        users    = _seed_users(session, roles)
        cats     = _seed_categories(session)
        tags     = _seed_tags(session)
        attrs    = _seed_attributes(session)
        products = _seed_products(session, cats, tags, attrs)
        coupons  = _seed_coupons(session)
        orders   = _seed_orders(session, users, products, coupons)
        _seed_reviews(session, users, products, orders)
        _seed_chatbot(session, users)
        session.commit()
        print("Seed complete!")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def _truncate(session):
    print("  Truncating tables...")
    tables = [
        "chatbot_feedback", "chatbot_responses", "chatbot_training_examples",
        "chatbot_intents", "chatbot_messages", "chatbot_conversations",
        "product_reviews", "order_items", "orders", "coupons",
        "product_tag", "product_faqs", "product_images",
        "product_variant_attributes", "product_variants", "products",
        "attribute_values", "attributes", "tags", "product_categories",
        "users", "roles",
    ]
    session.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    for t in tables:
        session.execute(text(f"TRUNCATE TABLE `{t}`"))
    session.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    session.commit()


# ── Roles ─────────────────────────────────────────────────────────────────────

def _seed_roles(session):
    print("  Roles...")
    data = [
        ("admin",    "Quan tri vien",  "Toan quyen he thong"),
        ("staff",    "Nhan vien",      "Quan ly don hang, san pham"),
        ("customer", "Khach hang",     "Mua sam"),
    ]
    roles = {}
    for name, display, desc in data:
        r = Role(name=name, display_name=display, description=desc)
        session.add(r); session.flush()
        roles[name] = r
    return roles


# ── Users ─────────────────────────────────────────────────────────────────────

VIET_NAMES = [
    # Group 1: Common Vietnamese names (A-B)
    "Nguyen Van An", "Nguyen Thi Mai", "Nguyen Van Bao", "Nguyen Thi Thuy",
    "Tran Van Manh", "Tran Thi Ha", "Tran Van Hung", "Tran Thi Huyen",
    "Le Van Tai", "Le Thi Thanh", "Le Van Duc", "Le Thi Huong",
    "Pham Van Minh", "Pham Thi Lan", "Pham Van Duy", "Pham Thi Nga",
    "Hoang Van Thanh", "Hoang Thi Yen", "Hoang Van Dat", "Hoang Thi Loan",
    "Vu Van Tien", "Vu Thi Trang", "Vu Van Chinh", "Vu Thi Thao",
    "Dang Van Phong", "Dang Thi Hong", "Dang Van Khoa", "Dang Thi Mai",
    "Bui Van Tuan", "Bui Thi Ngoc", "Bui Van Huy", "Bui Thi Hien",
    "Do Van Quang", "Do Thi Phuong", "Do Van Linh", "Do Thi Hoa",
    "Ngo Van Tuan", "Ngo Thi Thuy", "Ngo Van Phuc", "Ngo Thi Lan",
    # Group 2: More names (C-D)
    "Ly Van Thang", "Ly Thi Cam", "Ly Van Son", "Ly Thi Phuong",
    "Trinh Van Nam", "Trinh Thi Oanh", "Trinh Van Phat", "Trinh Thi Thuy",
    "Dinh Van Trung", "Dinh Thi Thuy", "Dinh Van Tuan", "Dinh Thi Huong",
    "Phan Van Duy", "Phan Thi Thao", "Phan Van Dat", "Phan Thi Nhung",
    "Cao Van Hoang", "Cao Thi Hoa", "Cao Van Phat", "Cao Thi Thuy",
    "Duong Van Chinh", "Duong Thi Mai", "Duong Van Dat", "Duong Thi Nga",
    "Luu Van Trung", "Luu Thi Thuy", "Luu Van Phuc", "Luu Thi Ngoc",
    "To Van Khanh", "To Thi Hien", "To Van Thanh", "To Thi Ha",
    "Ho Van Trung", "Ho Thi Huong", "Ho Van Dat", "Ho Thi Loan",
    "Vo Van Phuc", "Vo Thi Nga", "Vo Van Duy", "Vo Thi Thuy",
    # Group 3: More names (C-H)
    "Chau Van Vinh", "Chau Thi Xuan", "Chau Van Phong", "Chau Thi Hong",
    "Tang Van Thanh", "Tang Thi Van", "Tang Van Tri", "Tang Thi Nga",
    "Mac Van Quang", "Mac Thi Thuy", "Mac Van Dat", "Mac Thi Mai",
    "Kieu Van Tien", "Kieu Thi Nga", "Kieu Van Duy", "Kieu Thi Hoa",
    "Thai Van Hoang", "Thai Thi Thuy", "Thai Van Dat", "Thai Thi Nhung",
    "Lam Van Tai", "Lam Thi Thao", "Lam Van Duy", "Lam Thi Nga",
    "Truong Van Hoang", "Truong Thi Thuy", "Truong Van Dat", "Truong Thi Mai",
    "Huynh Van Duy", "Huynh Thi Thuy", "Huynh Van Tai", "Huynh Thi Loan",
    "Tong Van Duy", "Tong Thi Nga", "Tong Van Tai", "Tong Thi Ha",
    "Quach Van Duy", "Quach Thi Ngoc", "Quach Van Tai", "Quach Thi Thao",
    # Group 4: More names (H-K)
    "Doan Van Dat", "Doan Thi Huong", "Doan Van Tai", "Doan Thi Thao",
    "Nghiem Van Duy", "Nghiem Thi Thuy", "Nghiem Van Tai", "Nghiem Thi Mai",
    "Chu Van Duy", "Chu Thi Nga", "Chu Van Tai", "Chu Thi Hoa",
    "Ta Van Tai", "Ta Thi Ngoc", "Ta Van Dat", "Ta Thi Thuy",
    "Ma Van Tai", "Ma Thi Lan", "Ma Van Duy", "Ma Thi Thao",
    "Nong Van Tai", "Nong Thi Thuy", "Nong Van Dat", "Nong Thi Mai",
    "Ong Van Duy", "Ong Thi Huong", "Ong Van Tai", "Ong Thi Nga",
    "Phung Van Duy", "Phung Thi Thao", "Phung Van Tai", "Phung Thi Nhung",
    "Sam Van Duy", "Sam Thi Hoa", "Sam Van Tai", "Sam Thi Thuy",
    "Thach Van Duy", "Thach Thi Nga", "Thach Van Tai", "Thach Thi Mai",
    # Group 5: More names (K-M)
    "Ung Van Duy", "Ung Thi Thao", "Ung Van Tai", "Ung Thi Nga",
    "Vuong Van Duy", "Vuong Thi Thuy", "Vuong Van Tai", "Vuong Thi Hoa",
    "Xa Van Duy", "Xa Thi Nhung", "Xa Van Tai", "Xa Thi Mai",
    "Yen Van Duy", "Yen Thi Thao", "Yen Van Tai", "Yen Thi Nga",
    "Au Van Duy", "Au Thi Hoa", "Au Van Tai", "Au Thi Thuy",
    "Bach Van Duy", "Bach Thi Nga", "Bach Van Tai", "Bach Thi Mai",
    "Co Van Duy", "Co Thi Thuy", "Co Van Tai", "Co Thi Thao",
    "Du Van Duy", "Du Thi Nhung", "Du Van Tai", "Du Thi Hoa",
    "An Van Duy", "An Thi Thao", "An Van Tai", "An Thi Nga",
    "Bao Van Duy", "Bao Thi Mai", "Bao Van Tai", "Bao Thi Hoa",
    # Group 6: Additional common names
    "Nguyen Van Tri", "Nguyen Van Thinh", "Nguyen Van Hieu", "Nguyen Van Son",
    "Nguyen Van Cuong", "Nguyen Van Phong", "Nguyen Van Quang", "Nguyen Van Thang",
    "Nguyen Van Lam", "Nguyen Van Hiep", "Nguyen Van Chien", "Nguyen Van Luc",
    "Nguyen Van Khoi", "Nguyen Van Thuan", "Nguyen Van Hoa", "Nguyen Van Loc",
    "Tran Van Khoa", "Tran Van Luong", "Tran Van Kiet", "Tran Van Lam",
    "Tran Van Nhat", "Tran Van Binh", "Tran Van Phuc", "Tran Van Vinh",
    "Le Van Huy", "Le Van Khoi", "Le Van Nhat", "Le Van Binh",
    "Le Van Thuan", "Le Van Loc", "Le Van Lam", "Le Van Phuc",
    "Pham Van Nhat", "Pham Van Thinh", "Pham Van Hieu", "Pham Van Tri",
    "Pham Van Son", "Pham Van Cuong", "Pham Van Phong", "Pham Van Quang",
    # Group 7: Female names
    "Nguyen Thi Hien", "Nguyen Thi Thao", "Nguyen Thi Nhung", "Nguyen Thi Huong",
    "Nguyen Thi Loan", "Nguyen Thi Ngoc", "Nguyen Thi Trang", "Nguyen Thi Thuy",
    "Tran Thi My", "Tran Thi Lan", "Tran Thi Yen", "Tran Thi Oanh",
    "Tran Thi Thanh", "Tran Thi Phuong", "Tran Thi Hoai", "Tran Thi Nhi",
    "Le Thi My", "Le Thi Lan", "Le Thi Yen", "Le Thi Thao",
    "Le Thi Hoai", "Le Thi Nhi", "Le Thi Thuy", "Le Thi Nga",
    "Pham Thi Hien", "Pham Thi Thao", "Pham Thi Nhung", "Pham Thi Huong",
    "Pham Thi Loan", "Pham Thi Ngoc", "Pham Thi Trang", "Pham Thi Thuy",
    "Hoang Thi My", "Hoang Thi Lan", "Hoang Thi Yen", "Hoang Thi Oanh",
    "Hoang Thi Thanh", "Hoang Thi Phuong", "Hoang Thi Hoai", "Hoang Thi Nhi",
    # Group 8: More male names
    "Vu Van Huy", "Vu Van Khoi", "Vu Van Nhat", "Vu Van Binh",
    "Vu Van Thuan", "Vu Van Loc", "Vu Van Lam", "Vu Van Phuc",
    "Dang Van Huy", "Dang Van Khoi", "Dang Van Nhat", "Dang Van Binh",
    "Dang Van Thuan", "Dang Van Loc", "Dang Van Lam", "Dang Van Phuc",
    "Bui Van Huy", "Bui Van Khoi", "Bui Van Nhat", "Bui Van Binh",
    "Bui Van Thuan", "Bui Van Loc", "Bui Van Lam", "Bui Van Phuc",
    "Do Van Huy", "Do Van Khoi", "Do Van Nhat", "Do Van Binh",
    "Do Van Thuan", "Do Van Loc", "Do Van Lam", "Do Van Phuc",
    "Ngo Van Huy", "Ngo Van Khoi", "Ngo Van Nhat", "Ngo Van Binh",
    "Ngo Van Thuan", "Ngo Van Loc", "Ngo Van Lam", "Ngo Van Phuc",
    # Group 9: More diverse names
    "Ly Van Huy", "Ly Van Khoi", "Ly Van Nhat", "Ly Van Binh",
    "Trinh Van Huy", "Trinh Van Khoi", "Trinh Van Nhat", "Trinh Van Binh",
    "Dinh Van Huy", "Dinh Van Khoi", "Dinh Van Nhat", "Dinh Van Binh",
    "Phan Van Huy", "Phan Van Khoi", "Phan Van Nhat", "Phan Van Binh",
    "Cao Van Huy", "Cao Van Khoi", "Cao Van Nhat", "Cao Van Binh",
    "Duong Van Huy", "Duong Van Khoi", "Duong Van Nhat", "Duong Van Binh",
    "Luu Van Huy", "Luu Van Khoi", "Luu Van Nhat", "Luu Van Binh",
    "To Van Huy", "To Van Khoi", "To Van Nhat", "To Van Binh",
    "Ho Van Huy", "Ho Van Khoi", "Ho Van Nhat", "Ho Van Binh",
    "Vo Van Huy", "Vo Van Khoi", "Vo Van Nhat", "Vo Van Binh",
    # Group 10: Extended names
    "Chau Van Huy", "Chau Van Khoi", "Chau Van Nhat", "Chau Van Binh",
    "Tang Van Huy", "Tang Van Khoi", "Tang Van Nhat", "Tang Van Binh",
    "Mac Van Huy", "Mac Van Khoi", "Mac Van Nhat", "Mac Van Binh",
    "Kieu Van Huy", "Kieu Van Khoi", "Kieu Van Nhat", "Kieu Van Binh",
    "Thai Van Huy", "Thai Van Khoi", "Thai Van Nhat", "Thai Van Binh",
    "Lam Van Huy", "Lam Van Khoi", "Lam Van Nhat", "Lam Van Binh",
    "Truong Van Huy", "Truong Van Khoi", "Truong Van Nhat", "Truong Van Binh",
    "Huynh Van Huy", "Huynh Van Khoi", "Huynh Van Nhat", "Huynh Van Binh",
    "Tong Van Huy", "Tong Van Khoi", "Tong Van Nhat", "Tong Van Binh",
    "Quach Van Huy", "Quach Van Khoi", "Quach Van Nhat", "Quach Van Binh",
    # Group 11: Professional names
    "Doan Van Huy", "Doan Van Khoi", "Doan Van Nhat", "Doan Van Binh",
    "Nghiem Van Huy", "Nghiem Van Khoi", "Nghiem Van Nhat", "Nghiem Van Binh",
    "Chu Van Huy", "Chu Van Khoi", "Chu Van Nhat", "Chu Van Binh",
    "Ta Van Huy", "Ta Van Khoi", "Ta Van Nhat", "Ta Van Binh",
    "Ma Van Huy", "Ma Van Khoi", "Ma Van Nhat", "Ma Van Binh",
    "Nong Van Huy", "Nong Van Khoi", "Nong Van Nhat", "Nong Van Binh",
    "Ong Van Huy", "Ong Van Khoi", "Ong Van Nhat", "Ong Van Binh",
    "Phung Van Huy", "Phung Van Khoi", "Phung Van Nhat", "Phung Van Binh",
    "Sam Van Huy", "Sam Van Khoi", "Sam Van Nhat", "Sam Van Binh",
    "Thach Van Huy", "Thach Van Khoi", "Thach Van Nhat", "Thach Van Binh",
    # Group 12: Additional diverse names
    "Ung Van Huy", "Ung Van Khoi", "Ung Van Nhat", "Ung Van Binh",
    "Vuong Van Huy", "Vuong Van Khoi", "Vuong Van Nhat", "Vuong Van Binh",
    "Xa Van Huy", "Xa Van Khoi", "Xa Van Nhat", "Xa Van Binh",
    "Yen Van Huy", "Yen Van Khoi", "Yen Van Nhat", "Yen Van Binh",
    "Au Van Huy", "Au Van Khoi", "Au Van Nhat", "Au Van Binh",
    "Bach Van Huy", "Bach Van Khoi", "Bach Van Nhat", "Bach Van Binh",
    "Co Van Huy", "Co Van Khoi", "Co Van Nhat", "Co Van Binh",
    "Du Van Huy", "Du Van Khoi", "Du Van Nhat", "Du Van Binh",
    "An Van Huy", "An Van Khoi", "An Van Nhat", "An Van Binh",
    "Bao Van Huy", "Bao Van Khoi", "Bao Van Nhat", "Bao Van Binh",
    # Group 13: More unique names
    "Nguyen Van Phuc", "Nguyen Van Vu", "Nguyen Van Quan", "Nguyen Van Phu",
    "Nguyen Van Tan", "Nguyen Van Truong", "Nguyen Van Nghia", "Nguyen Van Hiep",
    "Tran Van Truong", "Tran Van Nghia", "Tran Van Hiep", "Tran Van Tan",
    "Le Van Truong", "Le Van Nghia", "Le Van Hiep", "Le Van Tan",
    "Pham Van Truong", "Pham Van Nghia", "Pham Van Hiep", "Pham Van Tan",
    "Hoang Van Truong", "Hoang Van Nghia", "Hoang Van Hiep", "Hoang Van Tan",
    "Vu Van Truong", "Vu Van Nghia", "Vu Van Hiep", "Vu Van Tan",
    "Dang Van Truong", "Dang Van Nghia", "Dang Van Hiep", "Dang Van Tan",
    "Bui Van Truong", "Bui Van Nghia", "Bui Van Hiep", "Bui Van Tan",
    "Do Van Truong", "Do Van Nghia", "Do Van Hiep", "Do Van Tan",
    # Group 14: District/street names
    "Le Van Luong", "Pham Van Dong", "To Ngoc Van", "Nguyen Van Cu",
    "Bui Xuan Duong", "Nguyen Van Tho", "Pham Van Chieu", "Nguyen Kim",
    "Tran Van Cu", "Pham Ngu Lao", "Nguyen Tri Phuong", "Thai Van Thanh",
    "Nguyen Van Lieu", "Tran Hung Dao", "Le Dai Hanh", "Ba Giai",
    "Nguyen Van Qua", "Truong Chinh", "Phan Van Tri", "Le Hong Phong",
    "Nguyen Van Tao", "Tran Binh Trong", "Le Van Duyet", "Nguyen Phuc",
    "Nguyen Van Ty", "Nguyen Van Dap", "Truong Van Dinh", "Nguyen Van Lo",
    "Luong Nhu Hieu", "Nguyen Cong Tru", "Nguyen Van Ty", "Ly Van Phuc",
]

STREETS = [
    "Nguyen Trai", "Le Van Sy", "Cach Mang Thang 8", "Dinh Tien Hoang",
    "Tran Hung Dao", "Nguyen Hue", "Le Loi", "Hai Ba Trung",
    "Phan Dinh Phung", "Vo Thi Sau", "Nguyen Dinh Chieu", "Ly Thuong Kiet",
    "Hoang Dieu", "Tran Phu", "Nguyen Cong Tru", "Ba Trieu",
    "Pham Van Dong", "To Ngoc Van", "Nguyen Van Cu", "Truong Chinh",
    "Phan Van Tri", "Le Hong Phong", "Le Dai Hanh", "Nguyen Kim",
    "Pham Ngu Lao", "Nguyen Tri Phuong", "Thai Van Thanh", "Bui Xuan Duong",
    "Nguyen Van Tho", "Pham Van Chieu", "Tran Binh Trong", "Le Van Duyet",
    "Luong Nhu Hieu", "Nguyen Phuc", "Nguyen Van Lo", "Truong Van Dinh",
    "Nguyen Van Ty", "Nguyen Van Dap", "Nguyen Van Qua", "Hoang Van Thuan",
    "Nguyen Van Bich", "Tran Van Cua", "Nguyen Van Lieu", "Le Van Luong",
    "Ba Giai", "Le Van Quyet", "Nguyen Van Mau", "Tran Quoc Toan",
    "Dong Khoi", "Nguyen Thai Hoc", "Ton That Thiet", "Le Ngoc Thach",
]

PROVINCES = [
    "Ha Noi", "TP. Ho Chi Minh", "Da Nang", "Hai Phong", "Can Tho",
    "Binh Duong", "Dong Nai", "Khanh Hoa", "Thua Thien Hue", "Quang Ninh",
    "Nghe An", "Thanh Hoa", "Bac Ninh", "Hai Duong", "Vinh Phuc",
    "Long An", "Tien Giang", "Ben Tre", "Vinh Long", "An Giang",
    "Dong Thap", "Tay Ninh", "Soc Trang", "Bac Lieu", "Ca Mau",
    "Lam Dong", "Dak Lak", "Gia Lai", "Dien Bien", "Lai Chau",
    "Son La", "Yen Bai", "Ha Giang", "Cao Bang", "Lao Cai",
    "Quang Nam", "Quang Ngai", "Binh Dinh", "Phu Yen", "Ninh Thuan",
    "Binh Thuan", "Kon Tum", "Quang Tri", "Ha Tinh", "Nam Dinh",
    "Ninh Binh", "Hung Yen", "Ha Nam", "Thai Binh", "Bac Kan",
    "Tuyen Quang", "Phu Tho", "Bac Giang", "Thai Nguyen", "Lang Son",
]

def _seed_users(session, roles):
    print(f"  Users ({len(VIET_NAMES)+3})...")
    users = []

    admin = User(
        name="Admin Shop", email="admin@shop.com",
        password=fake_password("admin123"), phone="0901234567",
        address="123 Nguyen Hue, Q1, TP.HCM",
        loyalty_points=0, role_id=roles["admin"].id, status="active",
        created_at=rand_date(400), updated_at=datetime.now()
    )
    session.add(admin); session.flush(); users.append(admin)

    for name, email, phone in [
        ("Nhan Vien A", "staff@shop.com",  "0912345678"),
        ("Nhan Vien B", "staff2@shop.com", "0923456789"),
    ]:
        s = User(
            name=name, email=email,
            password=fake_password("staff123"), phone=phone,
            address=f"{random.randint(1,500)} {random.choice(STREETS)}, TP.HCM",
            loyalty_points=0, role_id=roles["staff"].id, status="active",
            created_at=rand_date(300), updated_at=datetime.now()
        )
        session.add(s); session.flush(); users.append(s)

    for i, name in enumerate(VIET_NAMES):
        last = name.split()[-1].lower()
        email = f"{last}{i+1}@gmail.com"
        points = random.randint(0, 5000)
        status = random.choices(["active","inactive","banned"], weights=[82,15,3])[0]
        u = User(
            name=name, email=email,
            password=fake_password("password123"),
            phone=rand_phone(),
            address=f"{random.randint(1,999)} {random.choice(STREETS)}, {random.choice(PROVINCES)}",
            loyalty_points=points,
            role_id=roles["customer"].id,
            status=status,
            created_at=rand_date(500), updated_at=datetime.now()
        )
        session.add(u); session.flush(); users.append(u)

    return users


# ── Categories ────────────────────────────────────────────────────────────────

CAT_DATA = [
    ("Dien thoai & May tinh bang", "dien-thoai-may-tinh-bang", [
        ("Dien thoai", "dien-thoai"),
        ("May tinh bang", "may-tinh-bang"),
        ("Phu kien dien thoai", "phu-kien-dien-thoai"),
    ]),
    ("Laptop & May tinh", "laptop-may-tinh", [
        ("Laptop", "laptop"),
        ("May tinh de ban", "may-tinh-de-ban"),
        ("Phu kien may tinh", "phu-kien-may-tinh"),
    ]),
    ("Am thanh & Hinh anh", "am-thanh-hinh-anh", [
        ("Tai nghe", "tai-nghe"),
        ("Loa", "loa"),
        ("Dong ho thong minh", "dong-ho-thong-minh"),
        ("May anh", "may-anh"),
        ("Camera hanh trinh", "camera-hanh-trinh"),
    ]),
    ("My pham & Lam dep", "my-pham-lam-dep", [
        ("Cham soc da mat", "cham-soc-da-mat"),
        ("Trang diem", "trang-diem"),
        ("Nuoc hoa", "nuoc-hoa"),
        ("Cham soc toc", "cham-soc-toc"),
        ("Duong body", "duong-body"),
    ]),
    ("Thoi trang", "thoi-trang", [
        ("Ao", "ao"),
        ("Quan", "quan"),
        ("Giay dep", "giay-dep"),
        ("Tui xach", "tui-xach"),
        ("Phu kien thoi trang", "phu-kien-thoi-trang"),
        ("Do lot", "do-lot"),
    ]),
    ("Thuc pham & Do uong", "thuc-pham-do-uong", [
        ("Do an vat", "do-an-vat"),
        ("Do uong", "do-uong"),
        ("Thuc pham chuc nang", "thuc-pham-chuc-nang"),
        ("Thuc pham hieu qua", "thuc-pham-hieu-qua"),
    ]),
    ("Gia dung & Noi that", "gia-dung-noi-that", [
        ("Do gia dung", "do-gia-dung"),
        ("Noi that", "noi-that"),
        ("Do trang tri", "do-trang-tri"),
        ("Den trang tri", "den-trang-tri"),
    ]),
    ("The thao & Du lich", "the-thao-du-lich", [
        ("Thiet bi tap gym", "thiet-bi-tap-gym"),
        ("Do the thao", "do-the-thao"),
        ("Ba lo du lich", "ba-lo-du-lich"),
        ("Vali", "vali"),
        ("Do camping", "do-camping"),
    ]),
    ("Do choi & Game", "do-choi-game", [
        ("Game console", "game-console"),
        ("Game PC", "game-pc"),
        ("Do choi", "do-choi"),
        ("Do choi tri tue", "do-choi-tri-tue"),
    ]),
    ("Sach & Van phong pham", "sach-van-phong-pham", [
        ("Sach", "sach"),
        ("Van phong pham", "van-phong-pham"),
        ("Do dung hoc tap", "do-dung-hoc-tap"),
    ]),
    ("O to & Xe may", "o-to-xe-may", [
        ("Phu kien o to", "phu-kien-o-to"),
        ("Phu kien xe may", "phu-kien-xe-may"),
        ("Do bao hiem", "do-bao-hiem"),
    ]),
    ("Thu cuoi & Su kien", "thu-cuoi-su-kien", [
        ("Do thu cuoi", "do-thu-cuoi"),
        ("Trang tri su kien", "trang-tri-su-kien"),
        ("Qua tang", "qua-tang"),
    ]),
]

def _seed_categories(session):
    print("  Categories...")
    cats = {}
    for pname, pslug, children in CAT_DATA:
        parent = ProductCategory(
            name=pname, slug=pslug,
            description=f"Danh muc {pname}",
            is_active=True, order=len(cats),
            created_at=rand_date(600), updated_at=datetime.now()
        )
        session.add(parent); session.flush()
        cats[pslug] = parent
        for cname, cslug in children:
            child = ProductCategory(
                name=cname, slug=cslug,
                description=f"Danh muc con {cname}",
                parent_id=parent.id, is_active=True, order=len(cats),
                created_at=rand_date(600), updated_at=datetime.now()
            )
            session.add(child); session.flush()
            cats[cslug] = child
    return cats


# ── Tags ──────────────────────────────────────────────────────────────────────

TAG_NAMES = [
    "hot", "new", "sale", "bestseller", "limited", "flash-sale",
    "chinh-hang", "cao-cap", "gia-re", "trending", "yeu-thich",
    "qua-tang", "ben-dep", "nhap-khau", "organic", "vip", "exclusive",
    "hap-dan", "thoi-thuong", "phong-cach", "kien-tao", "sang-trong",
    "hau-truong", "thanh-lich", "mien-phi-van-chuyen", "tra-gop-0",
    "giam-gia-lon", "moi-nhat-2024", "hang-dat-mua", "thuong-hieu-noi-tieng",
    "xuat-khau", "chat-luong-cao", "do-ben", "nhieu-mau-sac",
]

def _seed_tags(session):
    print("  Tags...")
    tags = {}
    for name in TAG_NAMES:
        t = Tag(name=name, slug=name, created_at=rand_date(600), updated_at=datetime.now())
        session.add(t); session.flush()
        tags[name] = t
    return tags


# ── Attributes ────────────────────────────────────────────────────────────────

ATTR_DATA = {
    "Mau sac":    ("color",  ["Den", "Trang", "Xanh", "Do", "Vang", "Hong", "Tim", "Xam", "Bac", "Xanh Navy", "Xanh La", "Cam", "Be", "Kem", "Bạc", "Vang Gold"]),
    "Dung luong": ("select", ["64GB", "128GB", "256GB", "512GB", "1TB", "2TB"]),
    "RAM":        ("select", ["4GB", "8GB", "12GB", "16GB", "32GB", "64GB"]),
    "Size":       ("select", ["XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL"]),
    "Size giay":  ("select", ["35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46"]),
    "The tich":   ("select", ["250ml", "500ml", "1L", "1.5L", "2L"]),
    "Trong luong":("select", ["100g", "250g", "500g", "1kg", "2kg", "5kg"]),
    "Chat lieu":  ("select", ["Cotton", "Polyester", "Da", "Canvas", "Nylon", "Linh hoat"]),
    "Cong suat":  ("select", ["50W", "100W", "200W", "500W", "1000W", "2000W"]),
    "Pin":        ("select", ["3000mAh", "5000mAh", "10000mAh", "20000mAh"]),
    "Man hinh":   ("select", ["6.1 inch", "6.4 inch", "6.7 inch", "6.9 inch", "11 inch", "12.4 inch", "14 inch", "15.6 inch"]),
    "Do phan giai":("select", ["HD", "FHD", "2K", "4K", "8K"]),
}

def _seed_attributes(session):
    print("  Attributes...")
    attrs = {}
    for name, (atype, values) in ATTR_DATA.items():
        a = Attribute(
            name=name, slug=slugify(name), type=atype,
            is_filterable=True, is_active=True,
            created_at=rand_date(600), updated_at=datetime.now()
        )
        session.add(a); session.flush()
        avs = []
        for v in values:
            av = AttributeValue(
                attribute_id=a.id, value=v,
                order=values.index(v), is_active=True,
                created_at=rand_date(600), updated_at=datetime.now()
            )
            session.add(av); session.flush()
            avs.append(av)
        attrs[name] = (a, avs)
    return attrs


# ── Products ──────────────────────────────────────────────────────────────────
# (cat_slug, name, brand, origin, base_price, sale_pct, stock, description, variants_config)

PRODUCT_DATA = [
    # Dien thoai
    ("dien-thoai", "iPhone 15 Pro Max 256GB", "Apple", "My", 34990000, 5, 120,
     "iPhone 15 Pro Max chip A17 Pro, camera 48MP, man hinh 6.7 inch Super Retina XDR.",
     [("Mau sac", ["Den", "Trang", "Bac"]), ("Dung luong", ["256GB", "512GB"])]),

    ("dien-thoai", "iPhone 14 128GB", "Apple", "My", 18990000, 10, 200,
     "iPhone 14 chip A15 Bionic, camera kep 12MP, pin ben ca ngay.",
     [("Mau sac", ["Den", "Trang", "Hong", "Xanh"]), ("Dung luong", ["128GB", "256GB"])]),

    ("dien-thoai", "iPhone 13 128GB", "Apple", "My", 14990000, 15, 300,
     "iPhone 13 man hinh Super Retina XDR 6.1 inch, chip A15, camera kep cai tien.",
     [("Mau sac", ["Den", "Trang", "Hong", "Xanh", "Do"]), ("Dung luong", ["128GB", "256GB"])]),

    ("dien-thoai", "Samsung Galaxy S24 Ultra", "Samsung", "Han Quoc", 31990000, 8, 95,
     "Galaxy S24 Ultra but S Pen tich hop, camera 200MP, Dynamic AMOLED 6.8 inch.",
     [("Mau sac", ["Den", "Xam", "Xanh Navy"]), ("Dung luong", ["256GB", "512GB"])]),

    ("dien-thoai", "Samsung Galaxy S24+", "Samsung", "Han Quoc", 24990000, 10, 110,
     "Galaxy S24+ man hinh 6.7 inch AMOLED, chip Snapdragon 8 Gen 3, RAM 12GB.",
     [("Mau sac", ["Den", "Vang", "Xam"]), ("Dung luong", ["256GB", "512GB"])]),

    ("dien-thoai", "Samsung Galaxy A55 5G", "Samsung", "Han Quoc", 9990000, 12, 350,
     "Galaxy A55 5G Super AMOLED 6.6 inch, camera 50MP, RAM 8GB.",
     [("Mau sac", ["Den", "Trang", "Xanh", "Vang"]), ("Dung luong", ["128GB", "256GB"])]),

    ("dien-thoai", "Samsung Galaxy A35 5G", "Samsung", "Han Quoc", 7490000, 8, 280,
     "Galaxy A35 man hinh AMOLED 6.6 inch, camera 50MP, pin 5000mAh.",
     [("Mau sac", ["Den", "Xanh", "Hong"]), ("Dung luong", ["128GB", "256GB"])]),

    ("dien-thoai", "Xiaomi 14 Pro", "Xiaomi", "Trung Quoc", 22990000, 15, 80,
     "Xiaomi 14 Pro camera Leica, Snapdragon 8 Gen 3, sac nhanh 120W.",
     [("Mau sac", ["Den", "Trang", "Xanh"]), ("Dung luong", ["256GB", "512GB"])]),

    ("dien-thoai", "Xiaomi Redmi Note 13 Pro", "Xiaomi", "Trung Quoc", 8490000, 10, 400,
     "Redmi Note 13 Pro camera 200MP, AMOLED 120Hz, sac nhanh 67W.",
     [("Mau sac", ["Den", "Trang", "Xanh"]), ("Dung luong", ["128GB", "256GB"])]),

    ("dien-thoai", "OPPO Reno 11 5G", "OPPO", "Trung Quoc", 11490000, 10, 180,
     "OPPO Reno 11 camera AI 50MP, AMOLED 6.7 inch, pin 4800mAh.",
     [("Mau sac", ["Den", "Xanh", "Hong"]), ("Dung luong", ["256GB"])]),

    ("dien-thoai", "OPPO Find X7 Pro", "OPPO", "Trung Quoc", 28990000, 5, 60,
     "Find X7 Pro camera Hasselblad, Snapdragon 8 Gen 3, sac nhanh 100W.",
     [("Mau sac", ["Den", "Trang"]), ("Dung luong", ["256GB", "512GB"])]),

    ("dien-thoai", "Vivo V30e 5G", "Vivo", "Trung Quoc", 8490000, 0, 220,
     "Vivo V30e thiet ke mong nhe, camera chan dung, pin 5500mAh.",
     [("Mau sac", ["Den", "Xanh", "Hong"]), ("Dung luong", ["128GB", "256GB"])]),

    ("dien-thoai", "Realme 12 Pro+ 5G", "Realme", "Trung Quoc", 9990000, 18, 150,
     "Realme 12 Pro+ camera Periscope 3x zoom quang hoc, AMOLED 120Hz.",
     [("Mau sac", ["Den", "Xanh"]), ("Dung luong", ["256GB"])]),

    ("dien-thoai", "Nokia G42 5G", "Nokia", "Phan Lan", 5490000, 0, 300,
     "Nokia G42 5G ben IP52, pin 5000mAh, cap nhat Android lau dai.",
     [("Mau sac", ["Xanh", "Xam"]), ("Dung luong", ["128GB"])]),

    # May tinh bang
    ("may-tinh-bang", "iPad Pro M4 11 inch", "Apple", "My", 27990000, 5, 60,
     "iPad Pro M4 chip M4 sieu manh, Ultra Retina XDR, ho tro Apple Pencil Pro.",
     [("Dung luong", ["256GB", "512GB", "1TB"]), ("Mau sac", ["Bac", "Den"])]),

    ("may-tinh-bang", "iPad Air M2 11 inch", "Apple", "My", 18990000, 5, 80,
     "iPad Air M2 chip M2, man hinh Liquid Retina 11 inch, mong nhe.",
     [("Dung luong", ["128GB", "256GB"]), ("Mau sac", ["Bac", "Xanh", "Hong", "Vang"])]),

    ("may-tinh-bang", "iPad mini 6 256GB", "Apple", "My", 15990000, 8, 70,
     "iPad mini 6 man hinh 8.3 inch, chip A15, ket noi 5G.",
     [("Dung luong", ["64GB", "256GB"]), ("Mau sac", ["Bac", "Xam", "Hong", "Tim"])]),

    ("may-tinh-bang", "Samsung Galaxy Tab S9 FE", "Samsung", "Han Quoc", 10990000, 10, 90,
     "Galaxy Tab S9 FE S Pen di kem, 10.9 inch, chong nuoc IP68.",
     [("Dung luong", ["128GB", "256GB"]), ("Mau sac", ["Xam", "Xanh", "Trang"])]),

    ("may-tinh-bang", "Xiaomi Pad 6S Pro", "Xiaomi", "Trung Quoc", 12990000, 12, 75,
     "Xiaomi Pad 6S Pro 12.4 inch 144Hz, sac nhanh 67W, Snapdragon 8 Gen 2.",
     [("Dung luong", ["256GB", "512GB"]), ("Mau sac", ["Den", "Trang"])]),

    # Laptop
    ("laptop", "MacBook Air M3 13 inch", "Apple", "My", 32990000, 5, 45,
     "MacBook Air M3 mong nhe, pin 18 gio, Liquid Retina 13.6 inch.",
     [("RAM", ["8GB", "16GB"]), ("Dung luong", ["256GB", "512GB"])]),

    ("laptop", "MacBook Air M2 13 inch", "Apple", "My", 27990000, 8, 60,
     "MacBook Air M2 chip M2 hieu nang cao, man hinh Liquid Retina, khong quat.",
     [("RAM", ["8GB", "16GB"]), ("Dung luong", ["256GB", "512GB"])]),

    ("laptop", "MacBook Pro M3 Pro 14 inch", "Apple", "My", 52990000, 0, 30,
     "MacBook Pro M3 Pro ProMotion 120Hz, chip M3 Pro 12-core.",
     [("Dung luong", ["512GB", "1TB"])]),

    ("laptop", "Dell XPS 15 2024", "Dell", "My", 45990000, 8, 25,
     "Dell XPS 15 OLED 15.6 inch 3.5K, Intel Core Ultra 9, RTX 4070.",
     [("RAM", ["16GB", "32GB"]), ("Dung luong", ["512GB", "1TB"])]),

    ("laptop", "Dell Inspiron 15 3520", "Dell", "My", 14990000, 12, 90,
     "Dell Inspiron 15 Intel Core i5-1235U, RAM 8GB, man hinh FHD 120Hz.",
     [("RAM", ["8GB", "16GB"]), ("Dung luong", ["512GB"])]),

    ("laptop", "Asus ROG Zephyrus G14", "Asus", "Dai Loan", 38990000, 10, 35,
     "ROG Zephyrus G14 gaming AMD Ryzen 9, RTX 4060, 2.5K 165Hz.",
     [("RAM", ["16GB", "32GB"]), ("Dung luong", ["512GB", "1TB"])]),

    ("laptop", "Asus VivoBook 15 OLED", "Asus", "Dai Loan", 18990000, 10, 70,
     "VivoBook 15 OLED man hinh OLED 2.8K, Intel Core i5-13500H.",
     [("RAM", ["8GB", "16GB"]), ("Dung luong", ["512GB"])]),

    ("laptop", "Lenovo ThinkPad X1 Carbon Gen 12", "Lenovo", "Trung Quoc", 42990000, 5, 20,
     "ThinkPad X1 Carbon sieu nhe 1.12kg, MIL-SPEC, Intel Core Ultra 7.",
     [("RAM", ["16GB", "32GB"]), ("Dung luong", ["512GB", "1TB"])]),

    ("laptop", "Lenovo IdeaPad Slim 5i", "Lenovo", "Trung Quoc", 16990000, 10, 85,
     "IdeaPad Slim 5i Intel Core i5-13420H, OLED 2.8K, RAM 16GB.",
     [("RAM", ["8GB", "16GB"]), ("Dung luong", ["512GB"])]),

    ("laptop", "HP Pavilion 15 2024", "HP", "My", 16990000, 15, 80,
     "HP Pavilion 15 Intel Core i5-1335U, RAM 16GB, man hinh IPS.",
     [("RAM", ["8GB", "16GB"]), ("Dung luong", ["512GB"])]),

    ("laptop", "Acer Aspire 7 Gaming", "Acer", "Dai Loan", 18990000, 12, 65,
     "Acer Aspire 7 RTX 4050, Intel Core i5-13420H, man hinh 144Hz.",
     [("RAM", ["8GB", "16GB"]), ("Dung luong", ["512GB"])]),

    # Tai nghe
    ("tai-nghe", "Sony WH-1000XM5", "Sony", "Nhat Ban", 8490000, 15, 150,
     "Sony WH-1000XM5 chong on hang dau, am thanh LDAC, pin 30 gio.",
     [("Mau sac", ["Den", "Bac"])]),

    ("tai-nghe", "Sony WF-1000XM5", "Sony", "Nhat Ban", 6490000, 10, 130,
     "WF-1000XM5 tai nghe in-ear khong day, ANC hang dau, LDAC, pin 8 gio.",
     [("Mau sac", ["Den", "Bac"])]),

    ("tai-nghe", "Apple AirPods Pro 2nd Gen", "Apple", "My", 6490000, 8, 200,
     "AirPods Pro Gen 2 chip H2, ANC chu dong, chong nuoc IPX4.",
     [("Mau sac", ["Trang"])]),

    ("tai-nghe", "Apple AirPods 3rd Gen", "Apple", "My", 3990000, 5, 250,
     "AirPods Gen 3 thiet ke in-ear, spatial audio, chong nuoc IPX4.",
     [("Mau sac", ["Trang"])]),

    ("tai-nghe", "Samsung Galaxy Buds3 Pro", "Samsung", "Han Quoc", 4990000, 10, 180,
     "Galaxy Buds3 Pro ANC thong minh, Hi-Fi 24bit, pin 6 gio.",
     [("Mau sac", ["Den", "Trang", "Bac"])]),

    ("tai-nghe", "Bose QuietComfort 45", "Bose", "My", 7990000, 20, 90,
     "Bose QC45 chong on xuat sac, am bass manh, gap gon tien loi.",
     [("Mau sac", ["Den", "Trang"])]),

    ("tai-nghe", "JBL Tune 770NC", "JBL", "My", 2490000, 0, 250,
     "JBL Tune 770NC ANC hybrid, Pure Bass, pin 70 gio.",
     [("Mau sac", ["Den", "Trang", "Xanh", "Hong"])]),

    ("tai-nghe", "Jabra Evolve2 55", "Jabra", "Dan Mach", 9990000, 5, 40,
     "Jabra Evolve2 55 chuyen cho hoi nghi, ClearVoice, ket noi da diem.",
     [("Mau sac", ["Den"])]),

    # Loa
    ("loa", "JBL Charge 5", "JBL", "My", 3490000, 10, 120,
     "JBL Charge 5 chong nuoc IP67, pin 20 gio, 40W, co the sac dien thoai.",
     [("Mau sac", ["Den", "Xanh", "Do", "Xam"])]),

    ("loa", "JBL Flip 6", "JBL", "My", 2490000, 8, 200,
     "JBL Flip 6 chong nuoc IP67, pin 12 gio, am thanh stereo, ket noi 2 loa.",
     [("Mau sac", ["Den", "Xanh", "Do", "Hong", "Vang"])]),

    ("loa", "Sony SRS-XB100", "Sony", "Nhat Ban", 1190000, 0, 300,
     "Sony SRS-XB100 nho gon, chong nuoc IP67, pin 16 gio, Bluetooth 5.3.",
     [("Mau sac", ["Den", "Xanh", "Do", "Vang", "Hong"])]),

    ("loa", "Marshall Emberton II", "Marshall", "Anh", 4290000, 8, 70,
     "Marshall Emberton II thiet ke vintage, am thanh 3D song dong, pin 30 gio.",
     [("Mau sac", ["Den", "Trang"])]),

    ("loa", "Bose SoundLink Flex", "Bose", "My", 4990000, 5, 85,
     "Bose SoundLink Flex chong nuoc IP67, am thanh day du o ngoai troi.",
     [("Mau sac", ["Den", "Xanh"])]),

    # Dong ho thong minh
    ("dong-ho-thong-minh", "Apple Watch Series 9 45mm", "Apple", "My", 11990000, 5, 80,
     "Apple Watch S9 chip S9, Retina luon sang, phat hien va cham.",
     [("Mau sac", ["Den", "Bac", "Hong", "Vang"])]),

    ("dong-ho-thong-minh", "Apple Watch SE 2nd Gen 44mm", "Apple", "My", 7490000, 5, 100,
     "Apple Watch SE Gen 2 gia hap dan, chip S8, theo doi suc khoe ca ban.",
     [("Mau sac", ["Den", "Bac", "Vang"])]),

    ("dong-ho-thong-minh", "Samsung Galaxy Watch6 Classic 47mm", "Samsung", "Han Quoc", 8990000, 10, 60,
     "Galaxy Watch6 Classic bezel xoay lich lam, theo doi suc khoe toan dien.",
     [("Mau sac", ["Den", "Bac"])]),

    ("dong-ho-thong-minh", "Samsung Galaxy Watch6 40mm", "Samsung", "Han Quoc", 5990000, 8, 120,
     "Galaxy Watch6 nhe gon, sapphire crystal, theo doi giac ngu chinh xac.",
     [("Mau sac", ["Den", "Trang", "Vang"])]),

    ("dong-ho-thong-minh", "Garmin Venu 3", "Garmin", "My", 10990000, 5, 45,
     "Garmin Venu 3 theo doi suc khoe chuyen sau, pin 14 ngay, AMOLED.",
     [("Mau sac", ["Den", "Bac", "Trang"])]),

    ("dong-ho-thong-minh", "Xiaomi Smart Band 8 Pro", "Xiaomi", "Trung Quoc", 1590000, 15, 500,
     "Xiaomi Band 8 Pro AMOLED 1.74 inch, GPS, 150+ bai tap.",
     [("Mau sac", ["Den", "Xanh", "Trang"])]),

    # My pham
    ("cham-soc-da-mat", "Kem duong am Neutrogena Hydro Boost", "Neutrogena", "My", 389000, 0, 400,
     "Hydro Boost Hyaluronic Acid, tham hut nhanh, khong nhon, phu hop da dau.",
     [("Mau sac", ["Trang"])]),

    ("cham-soc-da-mat", "Serum Vitamin C La Roche-Posay", "La Roche-Posay", "Phap", 650000, 10, 250,
     "Serum Vitamin C 10% + E, lam sang da, chong oxy hoa, ket cau long nhe.",
     [("Mau sac", ["Trang"])]),

    ("cham-soc-da-mat", "Kem chong nang Anessa Perfect UV SPF50+", "Anessa", "Nhat Ban", 450000, 5, 350,
     "Anessa SPF50+ PA++++, Auto Booster ben trong nuoc va mo hoi.",
     [("Mau sac", ["Vang"])]),

    ("cham-soc-da-mat", "Tay trang Bioderma Sensibio H2O 500ml", "Bioderma", "Phap", 280000, 0, 600,
     "Tay trang diu nhe, khong can rua lai, phu hop da nhay cam.",
     [("Mau sac", ["Hong"])]),

    ("cham-soc-da-mat", "Mat na ngu Laneige Water Sleeping Mask", "Laneige", "Han Quoc", 690000, 8, 180,
     "Mat na ngu cung cap am toi da qua dem, SLEEPSCENT giup ngu ngon.",
     [("Mau sac", ["Xanh"])]),

    ("cham-soc-da-mat", "Sua rua mat CeraVe Foaming", "CeraVe", "My", 220000, 0, 500,
     "CeraVe Ceramide + Niacinamide, lam sach sau khong mat am.",
     [("Mau sac", ["Trang"])]),

    ("cham-soc-da-mat", "Tinh chat duong trang Melano CC", "Rohto", "Nhat Ban", 180000, 0, 700,
     "Melano CC Vitamin C dac tri tham nam, lam sang da, kha nang thau hut cao.",
     [("Mau sac", ["Trang"])]),

    ("nuoc-hoa", "Chanel Coco Mademoiselle EDP 100ml", "Chanel", "Phap", 4500000, 0, 30,
     "Coco Mademoiselle huong cam quyt tuoi mat, go dan huong am ap.",
     [("Mau sac", ["Vang"])]),

    ("nuoc-hoa", "Dior Sauvage EDT 100ml", "Dior", "Phap", 3800000, 5, 40,
     "Dior Sauvage manh me nam tinh, chanh Calabria va Ambroxan.",
     [("Mau sac", ["Xanh Navy"])]),

    ("nuoc-hoa", "Versace Bright Crystal EDT 90ml", "Versace", "Y", 1890000, 15, 80,
     "Bright Crystal huong hoa trai thanh thoat, luu huong ben, chai pha le dep.",
     [("Mau sac", ["Hong"])]),

    ("nuoc-hoa", "Yves Saint Laurent Black Opium EDP 90ml", "YSL", "Phap", 3200000, 0, 50,
     "YSL Black Opium huong cafe ngot ngao, vanilla va hoa trang bien.",
     [("Mau sac", ["Den"])]),

    ("trang-diem", "Son moi MAC Retro Matte", "MAC", "Canada", 650000, 5, 200,
     "MAC Retro Matte lau troi, mau ruc ro, chat li min khong kho moi.",
     [("Mau sac", ["Do", "Hong", "Xam", "Tim"])]),

    ("trang-diem", "Phan nen Maybelline Fit Me Matte", "Maybelline", "My", 185000, 0, 400,
     "Fit Me che phu trung binh, kiem dau 12 gio, 40 tong mau.",
     [("Mau sac", ["Trang", "Bac", "Vang"])]),

    ("trang-diem", "Mascara LOreal Telescopic Lift", "L'Oreal", "Phap", 220000, 0, 350,
     "LOreal Telescopic lam dai mi 66%, khong von cuc, ben 24 gio.",
     [("Mau sac", ["Den"])]),

    ("trang-diem", "Phan ma hong Romand Glasting Blush", "Romand", "Han Quoc", 280000, 0, 300,
     "Romand Glasting Blush kết cấu mỏng nhẹ, màu sắc rực rỡ lâu phai.",
     [("Mau sac", ["Hong", "Do", "Vang"])]),

    # Thoi trang
    ("ao", "Ao thun Uniqlo Supima Cotton", "Uniqlo", "Nhat Ban", 299000, 0, 500,
     "Ao thun Supima Cotton sieu mem min, form regular fit thoai mai.",
     [("Mau sac", ["Den", "Trang", "Xam", "Xanh Navy"]), ("Size", ["S", "M", "L", "XL", "XXL"])]),

    ("ao", "Ao polo Ralph Lauren Classic Fit", "Ralph Lauren", "My", 1290000, 10, 150,
     "Polo Ralph Lauren logo theu iconic, pique cotton mem min.",
     [("Mau sac", ["Trang", "Xanh", "Do", "Vang"]), ("Size", ["S", "M", "L", "XL"])]),

    ("ao", "Ao so mi Oxford Zara", "Zara", "Tay Ban Nha", 590000, 15, 200,
     "Zara Oxford day dan, slim fit tre trung, tui nguc theu logo.",
     [("Mau sac", ["Trang", "Xanh", "Xam"]), ("Size", ["S", "M", "L", "XL", "XXL"])]),

    ("ao", "Ao hoodie Champion Reverse Weave", "Champion", "My", 890000, 0, 180,
     "Champion fleece day, chu theu noi bat, form oversized am ap.",
     [("Mau sac", ["Den", "Xam", "Xanh Navy", "Do"]), ("Size", ["S", "M", "L", "XL", "XXL"])]),

    ("ao", "Ao khoac Adidas Tiro 23", "Adidas", "Duc", 790000, 10, 220,
     "Adidas Tiro 23 chat lieu recycled polyester, gio hat nuoc, form athletic.",
     [("Mau sac", ["Den", "Xanh Navy", "Do"]), ("Size", ["S", "M", "L", "XL", "XXL"])]),

    ("quan", "Quan jeans Levis 511 Slim", "Levi's", "My", 1490000, 10, 200,
     "Levis 511 ong dung slim fit, denim co gian 4 chieu.",
     [("Mau sac", ["Den", "Xanh", "Xam"]), ("Size", ["S", "M", "L", "XL", "XXL"])]),

    ("quan", "Quan khaki H&M Slim Chinos", "H&M", "Thuy Dien", 390000, 0, 300,
     "H&M chinos cotton pha spandex co gian nhe, lich su nang dong.",
     [("Mau sac", ["Den", "Xam", "Vang", "Xanh Navy"]), ("Size", ["S", "M", "L", "XL"])]),

    ("quan", "Quan short Nike Dri-FIT", "Nike", "My", 590000, 5, 350,
     "Nike Dri-FIT short van dong thoang mat, thoat hoi tot, phu hop tap gym.",
     [("Mau sac", ["Den", "Trang", "Xanh Navy"]), ("Size", ["S", "M", "L", "XL", "XXL"])]),

    # Giay dep
    ("giay-dep", "Giay Nike Air Force 1 Low", "Nike", "My", 2790000, 0, 250,
     "Air Force 1 Low thiet ke co dien, de Air dem em, da cao cap.",
     [("Mau sac", ["Trang", "Den"]), ("Size giay", ["38", "39", "40", "41", "42", "43", "44"])]),

    ("giay-dep", "Giay Nike Air Max 90", "Nike", "My", 3290000, 8, 180,
     "Air Max 90 de Air bubbly bieu tuong, thiet ke retro co dien.",
     [("Mau sac", ["Trang", "Den", "Do"]), ("Size giay", ["38", "39", "40", "41", "42", "43"])]),

    ("giay-dep", "Giay Adidas Ultraboost 23", "Adidas", "Duc", 3490000, 15, 150,
     "Ultraboost 23 dem Boost vo doi, sock-fit tien loi, thiet ke hien dai.",
     [("Mau sac", ["Den", "Trang", "Xanh"]), ("Size giay", ["38", "39", "40", "41", "42", "43"])]),

    ("giay-dep", "Giay Adidas Stan Smith", "Adidas", "Duc", 2190000, 5, 280,
     "Stan Smith trang bieu tuong, da cao cap, logo la xanh iconic.",
     [("Mau sac", ["Trang"]), ("Size giay", ["36", "37", "38", "39", "40", "41", "42", "43"])]),

    ("giay-dep", "Giay Converse Chuck Taylor All Star", "Converse", "My", 1390000, 5, 350,
     "Converse Chuck Taylor bieu tuong duong pho, canvas ben chac.",
     [("Mau sac", ["Den", "Trang", "Do", "Xanh Navy"]), ("Size giay", ["36", "37", "38", "39", "40", "41", "42"])]),

    ("giay-dep", "Sandal Birkenstock Arizona", "Birkenstock", "Duc", 2190000, 0, 100,
     "Birkenstock Arizona de cork dinh hinh ban chan, leather mem, cong thai hoc.",
     [("Mau sac", ["Den", "Vang", "Trang"]), ("Size giay", ["36", "37", "38", "39", "40", "41"])]),

    ("tui-xach", "Balo Samsonite Guardit Classy 15.6", "Samsonite", "Bi", 1890000, 10, 120,
     "Samsonite Guardit chong trom, ngan laptop 15.6, chong nuoc.",
     [("Mau sac", ["Den", "Xam"])]),

    ("tui-xach", "Tui tote Canvas Coach", "Coach", "My", 3490000, 8, 60,
     "Coach canvas chu ky iconic, quai da, ngan rong tien dung.",
     [("Mau sac", ["Den", "Xam", "Hong"])]),

    ("tui-xach", "Tui deo cheo Nike Heritage", "Nike", "My", 590000, 0, 400,
     "Nike Heritage deo cheo nhe gon, ngan chinh rong, thoang mat.",
     [("Mau sac", ["Den", "Xanh Navy", "Do"])]),

    # Thuc pham
    ("thuc-pham-chuc-nang", "Vitamin C 1000mg Blackmores", "Blackmores", "Uc", 320000, 5, 400,
     "Blackmores Vitamin C 1000mg tang de khang, hop 62 vien sui.",
     [("Mau sac", ["Vang"])]),

    ("thuc-pham-chuc-nang", "Omega-3 Fish Oil Nature Made", "Nature Made", "My", 280000, 0, 350,
     "Omega-3 1200mg DHA+EPA, tot cho tim mach nao bo, hop 100 vien.",
     [("Mau sac", ["Vang"])]),

    ("thuc-pham-chuc-nang", "Collagen DHC Beauty 60 ngay", "DHC", "Nhat Ban", 480000, 10, 200,
     "DHC Collagen 2500mg tu ca bien, lam dep da tu ben trong, 360 vien.",
     [("Mau sac", ["Hong"])]),

    ("thuc-pham-chuc-nang", "Whey Protein ON Gold Standard 2.27kg", "Optimum Nutrition", "My", 1890000, 5, 80,
     "ON Gold Standard 24g protein/lan, 5.5g BCAA, nhieu huong vi.",
     [("Mau sac", ["Trang"])]),

    ("thuc-pham-chuc-nang", "Vitamin tong hop Centrum Adults", "Centrum", "My", 250000, 0, 500,
     "Centrum Adults bổ sung 24 vitamin và khoáng chất thiết yếu, hop 100 vien.",
     [("Mau sac", ["Trang"])]),

    ("do-an-vat", "Khoai tay chien Pringles Original 165g", "Pringles", "My", 65000, 0, 1000,
     "Pringles Original gion tan dam da, hop tru tien loi.",
     [("Mau sac", ["Do"])]),

    ("do-an-vat", "Socola Kitkat 4 ngon hop 24 thanh", "Nestle", "Thuy Si", 175000, 8, 800,
     "Kitkat wafer gion phu socola sua, hop 24 thanh tiet kiem.",
     [("Mau sac", ["Do"])]),

    ("do-an-vat", "Hat dieu rang muoi Lafooco 500g", "Lafooco", "Viet Nam", 155000, 0, 500,
     "Hat dieu rang muoi to deu, gion thom, nhieu duong chat.",
     [("Mau sac", ["Vang"])]),

    ("do-an-vat", "Banh Oreo Original hop 432g", "Oreo", "My", 85000, 5, 900,
     "Oreo banh quy socola nhankem vanilla, hop 432g 18 goi nho.",
     [("Mau sac", ["Den"])]),

    ("do-uong", "Tra sua Phuc Long hop 220ml loc 6", "Phuc Long", "Viet Nam", 89000, 5, 800,
     "Tra sua Phuc Long huong tra dac trung thom ngon, tien loi uong lien.",
     [("Mau sac", ["Xanh"])]),

    ("do-uong", "Nuoc tang luc Redbull 250ml loc 24", "Redbull", "Ao", 420000, 0, 400,
     "Redbull tang luc tuc thi, caffeine + B-vitamins + taurine.",
     [("Mau sac", ["Xanh"])]),

    ("do-uong", "Nuoc khoang Evian 1.5L loc 12", "Evian", "Phap", 220000, 0, 600,
     "Nuoc khoang Evian nguon Alps, giau khoang chat, tiet kiem loc 12 chai.",
     [("Mau sac", ["Trang"])]),

    # Gia dung
    ("do-gia-dung", "Noi com Panasonic SR-HD184KRA 1.8L", "Panasonic", "Nhat Ban", 1490000, 10, 90,
     "Panasonic 1.8L diamond coating chong dinh, giu am 24h.",
     [("Mau sac", ["Trang", "Den"])]),

    ("do-gia-dung", "May xay sinh to Philips HR2041", "Philips", "Ha Lan", 890000, 5, 120,
     "Philips 450W luoi inox, coi 1.5L chiu nhiet, de ve sinh.",
     [("Mau sac", ["Trang", "Den"])]),

    ("do-gia-dung", "Ban la hoi nuoc Braun TexStyle 7", "Braun", "Duc", 1290000, 8, 60,
     "Braun 3000W, bom hoi 55g/phut, de FreeGlide kim cuong.",
     [("Mau sac", ["Xanh", "Trang"])]),

    ("do-gia-dung", "Noi chien khong dau Philips HD9270", "Philips", "Ha Lan", 2490000, 10, 80,
     "Philips Air Fryer HD9270 6.2L, Rapid Air 10 che do, nen thuc pham.",
     [("Mau sac", ["Den", "Trang"])]),

    ("do-gia-dung", "May hut bui Dyson V12 Detect Slim", "Dyson", "Anh", 13990000, 5, 30,
     "Dyson V12 laser phat hien bui silic, hut manh, pin 60 phut.",
     [("Mau sac", ["Vang", "Bac"])]),

    # May anh
    ("may-anh", "Sony Alpha A7 IV Body", "Sony", "Nhat Ban", 48990000, 8, 25,
     "Sony A7 IV 33MP full-frame, video 4K 60fps, AF 759 diem.",
     [("Mau sac", ["Den"])]),

    ("may-anh", "Canon EOS R6 Mark II Body", "Canon", "Nhat Ban", 54990000, 5, 20,
     "Canon R6 II 24.2MP, 40fps continuous shooting, IBIS.",
     [("Mau sac", ["Den"])]),

    ("may-anh", "Nikon Z8 Body", "Nikon", "Nhat Ban", 79990000, 0, 15,
     "Nikon Z8 45.7MP stacked sensor, 8K video, 120fps.",
     [("Mau sac", ["Den"])]),

    ("may-anh", "Fujifilm X-T5 Body", "Fujifilm", "Nhat Ban", 31990000, 10, 30,
     "Fujifilm X-T5 40.2MP, film simulations, compact body.",
     [("Mau sac", ["Den", "Xam", "Bac"])]),

    # Camera hanh trinh
    ("camera-hanh-trinh", "GoPro Hero 12 Black", "GoPro", "My", 11990000, 10, 60,
     "GoPro Hero 12 Black 5.3K video, HyperSmooth 6.0, waterproof 10m.",
     [("Mau sac", ["Den"])]),

    ("camera-hanh-trinh", "Insta360 X4", "Insta360", "Trung Quoc", 15990000, 8, 40,
     "Insta360 X4 8K 360 camera, AI editing, waterproof 10m.",
     [("Mau sac", ["Den"])]),

    ("camera-hanh-trinh", "DJI Osmo Action 4", "DJI", "Trung Quoc", 9990000, 12, 50,
     "DJI Action 4 4K 120fps, 10-bit, waterproof 18m.",
     [("Mau sac", ["Den", "Xam"])]),

    # Tai nghe (them)
    ("tai-nghe", "Samsung Galaxy Buds2 Pro", "Samsung", "Han Quoc", 3990000, 15, 200,
     "Galaxy Buds2 Pro ANC, Hi-Fi 24bit, khong Gian 3D.",
     [("Mau sac", ["Den", "Trang", "Bac"])]),

    ("tai-nghe", "Sennheiser Momentum 4 Wireless", "Sennheiser", "Duc", 8990000, 5, 35,
     "Sennheiser M4 am thanh xuat sac, Adaptive ANC, pin 60 gio.",
     [("Mau sac", ["Den", "Trang"])]),

    # Dong ho thong minh (them)
    ("dong-ho-thong-minh", "Samsung Galaxy Watch7 44mm", "Samsung", "Han Quoc", 7990000, 8, 70,
     "Galaxy Watch7 Exynos W930, theo doi suc khoe AI, LTE.",
     [("Mau sac", ["Den", "Xanh", "Trang"])]),

    ("dong-ho-thong-minh", "Garmin Forerunner 965", "Garmin", "My", 14990000, 0, 25,
     "Garmin Forerunner 965 GPS, AMOLED, theo doi hieu qua tap luyen.",
     [("Mau sac", ["Den", "Trang"])]),

    ("dong-ho-thong-minh", "Huawei Watch GT 4 46mm", "Huawei", "Trung Quoc", 5990000, 10, 80,
     "Huawei GT 4 14 ngay pin, 100+ che do the thao, AMOLED.",
     [("Mau sac", ["Den", "Bac", "Vang"])]),

    # Cham soc toc
    ("cham-soc-toc", "May say toc Dyson Supersonic", "Dyson", "Anh", 11990000, 5, 30,
     "Dyson Supersonic cong nghe ion, 110000rpm, cham soc toc.",
     [("Mau sac", ["Den", "Trang", "Hong"])]),

    ("cham-soc-toc", "May uon toc Panasonic EH-HS99", "Panasonic", "Nhat Ban", 2490000, 10, 80,
     "Panasonic uon toc tu dong, ceramic, nhiet do on dinh.",
     [("Mau sac", ["Den", "Trang"])]),

    ("cham-soc-toc", "Duong toc Kérastase Elixir Ultime", "Kerastase", "Phap", 890000, 8, 150,
     "Kerastase Elixir dưỡng óng ánh, hàm lượng dầu cao, 100ml.",
     [("Mau sac", ["Vang"])]),

    # Duong body
    ("duong-body", "Sữa dưỡng thể Vaseline Healthy Bright", "Vaseline", "My", 189000, 0, 400,
     "Vaseline dưỡng ẩm, làm sáng da, Vitamin B3.",
     [("Mau sac", ["Trang"])]),

    ("duong-body", "Gel tắm Dove Deep Moisture", "Dove", "My", 125000, 0, 500,
     "Dove gel tắm dưỡng ẩm 24h, công thức nhẹ.",
     [("Mau sac", ["Trang", "Hồng"])]),

    # Do the thao
    ("do-the-thao", "Bộ yoga Lululemon Align", "Lululemon", "Canada", 1890000, 8, 100,
     "Lululemon Align Nulu mềm như da thứ hai, co giãn 4 chiều.",
     [("Mau sac", ["Đen", "Xanh", "Tím", "Hồng"]), ("Size", ["XS", "S", "M", "L", "XL"])]),

    ("do-the-thao", "Giày chạy bộ Nike Pegasus 40", "Nike", "My", 2890000, 10, 150,
     "Nike Pegasus 40 Air Zoom, thoáng khí, đệm React.",
     [("Mau sac", ["Đen", "Trắng", "Xanh", "Hồng"]), ("Size giay", ["38", "39", "40", "41", "42", "43"])]),

    ("do-the-thao", "Balo thể thao Adidas Essentials", "Adidas", "Duc", 790000, 15, 200,
     "Adidas Essentials 30L, nhiều ngăn, vải chống nước.",
     [("Mau sac", ["Đen", "Xanh", "Xám"])]),

    # Vali
    ("vali", "Vali kéo Samsonite Winfield 3", "Samsonite", "Bi", 3490000, 10, 80,
     "Samsonite PC 20 inch, 4 bánh xe xoay, khóa TSA.",
     [("Mau sac", ["Đen", "Xanh", "Bạc", "Hồng"])]),

    ("vali", "Vali kéo American Tourister Curv", "American Tourister", "Bi", 2890000, 12, 100,
     "AT Curv 24 inch, nhẹ bền, thiết kế hiện đại.",
     [("Mau sac", ["Đen", "Xanh", "Tím"])]),

    # Ba lo du lich
    ("ba-lo-du-lich", "Ba lo Herschel Little America", "Herschel", "Canada", 1890000, 5, 80,
     "Herschel 25L foam, laptop 15 inch, phong cách vintage.",
     [("Mau sac", ["Đen", "Xanh", "Nâu"])]),

    # Do camping
    ("do-camping", "Lều cắm trại Naturehike Cloud Up 2", "Naturehike", "Trung Quoc", 2890000, 8, 40,
     "Naturehike 2 người, nhẹ 1.5kg, chống nước 3000mm.",
     [("Mau sac", ["Xanh", "Cam", "Vàng"])]),

    ("do-camping", "Túi ngủ naturehike -10°C", "Naturehike", "Trung Quoc", 1490000, 10, 60,
     "Túi ngủ mùa đông, nhẹ ấm, chất liệu nylon.",
     [("Mau sac", ["Xanh", "Cam"])]),

    # Game console
    ("game-console", "Sony PlayStation 5 Slim", "Sony", "Nhat Ban", 12990000, 5, 30,
     "PS5 Slim 1TB SSD, ray tracing, haptic feedback.",
     [("Mau sac", ["Trắng"])]),

    ("game-console", "Microsoft Xbox Series X", "Microsoft", "My", 11990000, 8, 35,
     "Xbox Series X 12 TFLOPS, 4K 120fps, Quick Resume.",
     [("Mau sac", ["Đen"])]),

    ("game-console", "Nintendo Switch OLED", "Nintendo", "Nhat Ban", 8490000, 5, 50,
     "Switch OLED 7 inch, màn hình OLED, dock có dây LAN.",
     [("Mau sac", ["Trắng", "Đen", "Neon Red/Blue"])]),

    # Game PC
    ("game-pc", "Tai nghe gaming HyperX Cloud III", "HyperX", "My", 1490000, 10, 120,
     "HyperX Cloud III 7.1 surround, mic detachable, memory foam.",
     [("Mau sac", ["Đen", "Đỏ", "Xanh"])]),

    ("game-pc", "Ban phim cơ Razer BlackWidow V4 Pro", "Razer", "My", 4190000, 8, 40,
     "Razer V4 Pro green switches, RGB, knob đa chức năng.",
     [("Mau sac", ["Đen"])]),

    ("game-pc", "Chuột gaming Logitech G Pro X Superlight 2", "Logitech", "My", 2790000, 10, 60,
     "G Pro X 2 60g, HERO 2 sensor, 32k DPI, pin 90h.",
     [("Mau sac", ["Đen", "Trắng", "Hồng"])]),

    # Do choi
    ("do-choi", "Lego Star Wars Millennium Falcon", "Lego", "Denmark", 7890000, 0, 20,
     "Lego 7541 mảnh, minifigures 7 nhân vật, chi tiết cao.",
     [("Mau sac", ["Xám"])]),

    ("do-choi", "Bộ xếp hình Lego City", "Lego", "Denmark", 590000, 0, 150,
     "Lego City 60349 xe cứu hỏa, 296 mảnh, trẻ em 5+.",
     [("Mau sac", ["Đỏ"])]),

    # Do choi tri tue
    ("do-choi-tri-tieu", "Rubik's Cube 3x3 speed", "Rubik's", "My", 250000, 0, 300,
     "Rubik 3x3 xoay mượt, dán nhãn tốc độ, bền bỉ.",
     [("Mau sac", ["Nhiều màu"])]),

    # Sach
    ("sach", "Đắc Nhân Tâm - Dale Carnegie", "First News", "Viet Nam", 79000, 0, 500,
     "Đắc Nhân Tâm bản tiếng Việt, sách kinh điển.",
     [("Mau sac", ["Vàng"])]),

    ("sach", "Atomic Habits - James Clear", "First News", "My", 169000, 10, 300,
     "Atomic Habits thay đổi thói quen, tư duy sống.",
     [("Mau sac", ["Vàng"])]),

    ("sach", "Sách Lập trình Python", "O'Reilly", "My", 350000, 0, 200,
     "Python crash course lập trình căn bản đến nâng cao.",
     [("Mau sac", ["Xanh"])]),

    # Van phong pham
    ("van-phong-pham", "Bút Pilot G2 07", "Pilot", "Nhat Ban", 15000, 0, 1000,
     "Pilot G2 mượt, mực gel, nhiều màu.",
     [("Mau sac", ["Đen", "Xanh", "Đỏ"])]),

    ("van-phong-pham", "Sổ Moleskine Classic", "Moleskine", "Y", 290000, 5, 300,
     "Moleskine 176 trang, giấy tốt, bìa cứng.",
     [("Mau sac", ["Đen", "Đỏ", "Xanh"])]),

    ("van-phong-pham", "Máy tính Casio FX-580VN", "Casio", "Nhat Ban", 450000, 0, 400,
     "Casio 580 522 tính năng, thiết kế mới.",
     [("Mau sac", ["Đen"])]),

    # Do dung hoc tap
    ("do-dung-hoc-tap", "Bàn học sinh chống gù", "Flexa", "Viet Nam", 2490000, 10, 60,
     "Bàn chống gù có kệ sách, điều chỉnh độ cao.",
     [("Mau sac", ["Trắng", "Gỗ"])]),

    # Phu kien o to
    ("phu-kien-o-to", "Camera lùi Ô tô Vietmap", "Vietmap", "Viet Nam", 890000, 15, 200,
     "Vietmap camera lùi HD, gương chiếu hậu.",
     [("Mau sac", ["Đen"])]),

    ("phu-kien-o-to", "Máy hút ẩm ô tô", "Xiaomi", "Trung Quoc", 590000, 12, 150,
     "Xiaomi hút ẩm mini 12V, tự động ngắt.",
     [("Mau sac", ["Đen"])]),

    ("phu-kien-o-to", "Cảm biến áp suất lốp TPMS", "Xiaomi", "Trung Quoc", 690000, 10, 100,
     "TPMS giám sát áp suất lốp, màn hình LCD.",
     [("Mau sac", ["Đen"])]),

    # Phu kien xe may
    ("phu-kien-xe-may", "Mũ bảo hiểm Yohe 958", "Yohe", "Trung Quoc", 690000, 15, 300,
     "Yohe nửa đầu kính, chất liệu ABS.",
     [("Mau sac", ["Đen", "Trắng", "Đỏ", "Xanh"])]),

    ("phu-kien-xe-may", "Găng tay xe máy MotoGP", "Racing", "Trung Quoc", 390000, 10, 250,
     "Găng tay chống va, thoáng khí, bảo vệ ngón.",
     [("Mau sac", ["Đen", "Xám"])]),

    # Do bao hiem
    ("do-bao-hiem", "Bộ đồ bảo hộ motoRider Pro", "MotoRider", "Viet Nam", 1290000, 8, 80,
     "Bộ bảo hộ full chất liệu cao cấp, thoáng khí.",
     [("Mau sac", ["Đen", "Xám"])]),

    # Do thu cuoi
    ("do-thu-cuoi", "Váy cưới cao cấp", "Sanh Tieu", "Viet Nam", 8990000, 0, 20,
     "Váy cưới ren hoa tay dài, phong cách vintage.",
     [("Mau sac", ["Trắng", "Kem"])]),

    ("do-thu-cuoi", "Suit nam cưới", "An Phước", "Viet Nam", 3990000, 0, 30,
     "Suit cưới nam cao cấp, may đo chuẩn.",
     [("Mau sac", ["Đen", "Xám", "Xanh Navy"])]),

    # Qua tang
    ("qua-tang", "Hộp quà tết cao cấp", "Tư Mỹ", "Viet Nam", 590000, 5, 200,
     "Hộp quà Tết bánh kẹo cao cấp, trang trí sang trọng.",
     [("Mau sac", ["Đỏ", "Vàng"])]),

    ("qua-tang", "Bình hoa trang trí", "IKEA", "Thụy Điển", 390000, 0, 150,
     "IKEA vase SONGESAND thủy tinh, hiện đại.",
     [("Mau sac", ["Trắng", "Xám"])]),

    # Trang tri su kien
    ("trang-tri-su-kien", "Bóng đèn trang trí", "Philips", "Ha Lan", 89000, 0, 500,
     "Philips Hue LED decor, đổi màu, điều khiển app.",
     [("Mau sac", ["Nhiều màu"])]),

    # Do trang tri
    ("do-trang-tri", "Đèn bàn học LED", "BenQ", "Đài Loan", 1290000, 10, 80,
     "BenQ ScreenBar Plus, cảm biến, không chói.",
     [("Mau sac", ["Đen"])]),

    ("do-trang-tri", "Khung tranh treo tường", "IKEA", "Thụy Điển", 290000, 0, 200,
     "IKEA RIBBA khung tranh, nhiều size.",
     [("Mau sac", ["Đen", "Trắng", "Gỗ"])]),

    # Den trang tri
    ("den-trang-tri", "Đèn trần hiện đại", "Philips", "Ha Lan", 2490000, 10, 50,
     "Philips LED trần 50W, điều khiển từ xa.",
     [("Mau sac", ["Trắng"])]),

    ("den-trang-tri", "Đèn ngủ cảm ứng", "Xiaomi", "Trung Quoc", 390000, 15, 300,
     "Xiaomi ngủ cảm ứng chạm, đổi màu, pin 48h.",
     [("Mau sac", ["Trắng", "Vàng", "Xanh"])]),

    # Thuc pham hieu qua
    ("thuc-pham-hieu-qua", "Sữa tươi Enikin 1L", "Vinamilk", "Viet Nam", 35000, 0, 1000,
     "Vinamilk sữa tươi tiệt trùng, giàu canxi.",
     [("Mau sac", ["Trắng"])]),

    ("thuc-pham-hieu-qua", "Mật ong hoa vải", "Sao Cửu Long", "Viet Nam", 180000, 0, 400,
     "Mật ong nguyên chất 500g, thơm ngọt.",
     [("Mau sac", ["Vàng"])]),

    ("thuc-pham-hieu-qua", "Cà phê rang xay G7 3 in 1", "Nestle", "Viet Nam", 45000, 0, 800,
     "G7 3 in 1 hòa tan đậm đà, tiện lợi.",
     [("Mau sac", ["Nâu"])]),

    # === ADDITIONAL PRODUCTS FOR DIVERSITY ===

    # --- Dien thoai (more) ---
    ("dien-thoai", "iPhone 16 Pro Max 256GB", "Apple", "My", 38990000, 0, 100,
     "iPhone 16 Pro Max chip A18 Pro, camera 48MP, Action Button.",
     [("Mau sac", ["Den", "Trang", "Xam"]), ("Dung luong", ["256GB", "512GB", "1TB"])]),

    ("dien-thoai", "iPhone 16 128GB", "Apple", "My", 22990000, 5, 150,
     "iPhone 16 chip A18, Dynamic Island, camera 48MP.",
     [("Mau sac", ["Den", "Trang", "Xanh", "Hong"]), ("Dung luong", ["128GB", "256GB"])]),

    ("dien-thoai", "Samsung Galaxy Z Fold6", "Samsung", "Han Quoc", 41990000, 8, 50,
     "Galaxy Z Fold6 foldable 7.6 inch, S Pen, AI features.",
     [("Mau sac", ["Den", "Xanh", "Trang"]), ("Dung luong", ["256GB", "512GB"])]),

    ("dien-thoai", "Samsung Galaxy Z Flip6", "Samsung", "Han Quoc", 24990000, 10, 80,
     "Galaxy Z Flip6 compact foldable, FlexMode camera.",
     [("Mau sac", ["Den", "Xanh", "Trang", "Hong"]), ("Dung luong", ["256GB", "512GB"])]),

    ("dien-thoai", "Google Pixel 9 Pro", "Google", "My", 27990000, 5, 60,
     "Pixel 9 Pro Tensor G4, camera AI, 7 years updates.",
     [("Mau sac", ["Den", "Trang", "Xam"]), ("Dung luong", ["128GB", "256GB", "512GB"])]),

    ("dien-thoai", "Google Pixel 8a", "Google", "My", 14990000, 10, 100,
     "Pixel 8a mid-range AI phone, 7 years updates.",
     [("Mau sac", ["Den", "Trang", "Xanh"]), ("Dung luong", ["128GB", "256GB"])]),

    ("dien-thoai", "OnePlus 12", "OnePlus", "Trung Quoc", 22990000, 8, 70,
     "OnePlus 12 Snapdragon 8 Gen 3, 100W charging.",
     [("Mau sac", ["Den", "Trang", "Xanh"]), ("Dung luong", ["256GB", "512GB"])]),

    ("dien-thoai", "Huawei Mate 60 Pro", "Huawei", "Trung Quoc", 26990000, 0, 40,
     "Mate 60 Pro Kirin 9000s, satellite calling.",
     [("Mau sac", ["Den", "Trang", "Vang"]), ("Dung luong", ["256GB", "512GB", "1TB"])]),

    ("dien-thoai", "POCO F6 Pro", "Xiaomi", "Trung Quoc", 14990000, 12, 120,
     "POCO F6 Pro Snapdragon 8 Gen 2, 120W charging.",
     [("Mau sac", ["Den", "Trang"]), ("Dung luong", ["256GB", "512GB"])]),

    ("dien-thoai", "Infinix Note 40 Pro", "Infinix", "Trung Quoc", 6990000, 15, 200,
     "Infinix Note 40 Pro AMOLED, 108MP camera.",
     [("Mau sac", ["Den", "Vang", "Xanh"]), ("Dung luong", ["256GB"])]),

    # --- May tinh bang (more) ---
    ("may-tinh-bang", "iPad 10th Gen 256GB", "Apple", "My", 15990000, 8, 90,
     "iPad 10 A14 Bionic, 10.9 inch Liquid Retina.",
     [("Dung luong", ["64GB", "256GB"]), ("Mau sac", ["Xanh", "Hong", "Trang", "Vang"])]),

    ("may-tinh-bang", "Samsung Galaxy Tab S9 Ultra 5G", "Samsung", "Han Quoc", 32990000, 5, 40,
     "Galaxy Tab S9 Ultra 14.6 inch, S Pen, 5G.",
     [("Dung luong", ["256GB", "512GB"]), ("Mau sac", ["Den"])]),

    ("may-tinh-bang", "OnePlus Pad 2", "OnePlus", "Trung Quoc", 17990000, 10, 50,
     "OnePlus Pad 2 12.1 inch 144Hz, Snapdragon 8 Gen 3.",
     [("Dung luong", ["128GB", "256GB"]), ("Mau sac", ["Xam"])]),

    ("may-tinh-bang", "Lenovo Tab P12 Pro", "Lenovo", "Trung Quoc", 14990000, 8, 60,
     "Tab P12 Pro 12.6 inch AMOLED, 120Hz, keyboard optional.",
     [("Dung luong", ["256GB"]), ("Mau sac", ["Den", "Trang"])]),

    # --- Laptop (more) ---
    ("laptop", "MacBook Pro M3 Max 16 inch", "Apple", "My", 99990000, 0, 15,
     "MacBook Pro M3 Max 16-core CPU, 40-core GPU, 128GB RAM.",
     [("RAM", ["36GB", "64GB", "96GB", "128GB"]), ("Dung luong", ["1TB", "2TB", "4TB"])]),

    ("laptop", "MacBook Air 15 inch M3", "Apple", "My", 30990000, 5, 50,
     "MacBook Air 15 M3 15.3 inch, liquid retina, fanless.",
     [("RAM", ["8GB", "16GB", "24GB"]), ("Dung luong", ["256GB", "512GB", "1TB"])]),

    ("laptop", "Dell XPS 13 Plus 2024", "Dell", "My", 32990000, 8, 30,
     "XPS 13 Plus OLED 13.4 inch, Intel Core Ultra 7, haptic touchpad.",
     [("RAM", ["16GB", "32GB"]), ("Dung luong", ["512GB", "1TB"])]),

    ("laptop", "HP Spectre x360 16", "HP", "My", 42990000, 5, 20,
     "Spectre x360 16 2-in-1, OLED 120Hz, Intel Core Ultra 7.",
     [("RAM", ["16GB", "32GB"]), ("Dung luong", ["512GB", "1TB"])]),

    ("laptop", "Asus ROG Strix G16", "Asus", "Dai Loan", 32990000, 10, 40,
     "ROG Strix G16 Intel Core i9-14900HX, RTX 4080.",
     [("RAM", ["16GB", "32GB"]), ("Dung luong", ["1TB", "2TB"])]),

    ("laptop", "Asus ZenBook Pro 16X", "Asus", "Dai Loan", 45990000, 5, 25,
     "ZenBook Pro 16X OLED, Intel Core i9, RTX 4080.",
     [("RAM", ["16GB", "32GB"]), ("Dung luong", ["1TB", "2TB"])]),

    ("laptop", "Lenovo Legion Pro 7i", "Lenovo", "Trung Quoc", 54990000, 8, 20,
     "Legion Pro 7i Intel Core i9-14900HX, RTX 4080, 240Hz.",
     [("RAM", ["16GB", "32GB", "64GB"]), ("Dung luong", ["1TB", "2TB"])]),

    ("laptop", "MSI Titan GT77 HX", "MSI", "Dai Loan", 89990000, 0, 10,
     "MSI Titan GT77 17.3 inch 4K 144Hz, i9-14900HX, RTX 4090.",
     [("RAM", ["64GB", "128GB"]), ("Dung luong", ["2TB", "4TB"])]),

    ("laptop", "Razer Blade 16", "Razer", "My", 69990000, 5, 15,
     "Razer Blade 16 OLED 240Hz, i9-13950HX, RTX 4080.",
     [("RAM", ["16GB", "32GB", "64GB"]), ("Dung luong", ["1TB", "2TB"])]),

    ("laptop", "Gigabyte Aorus 17X", "Gigabyte", "Dai Loan", 54990000, 8, 20,
     "Aorus 17X Intel Core i9-14900HX, RTX 4090, 300Hz.",
     [("RAM", ["16GB", "32GB", "64GB"]), ("Dung luong", ["1TB", "2TB", "4TB"])]),

    # --- Tai nghe (more) ---
    ("tai-nghe", "Beats Studio Pro", "Beats", "My", 7990000, 10, 100,
     "Beats Studio Pro custom acoustic platform, 40h battery.",
     [("Mau sac", ["Den", "Trang", "Xanh", "Be"])]),

    ("tai-nghe", "Beats Fit Pro", "Beats", "My", 4990000, 8, 150,
     "Beats Fit Pro ear hooks, ANC, IPX4 water resistant.",
     [("Mau sac", ["Den", "Trang", "Xanh", "Tim", "Be"])]),

    ("tai-nghe", "Samsung Galaxy Buds FE", "Samsung", "Han Quoc", 1990000, 15, 300,
     "Galaxy Buds FE affordable, ANC, 21h battery.",
     [("Mau sac", ["Den", "Trang"])]),

    ("tai-nghe", "Anker Soundcore Space Q45", "Anker", "Trung Quoc", 2990000, 15, 200,
     "Soundcore Q45 LDAC, ANC 98%, 50h battery.",
     [("Mau sac", ["Den", "Trang"])]),

    ("tai-nghe", "Shure AONIC 50 Gen 2", "Shure", "My", 10990000, 5, 30,
     "Shure AONIC 50 Gen 2 studio quality, 45h battery.",
     [("Mau sac", ["Den", "Trang"])]),

    ("tai-nghe", "Bang & Olufsen Beoplay H95", "Bang & Olufsen", "Dan Mach", 18990000, 0, 15,
     "B&O H95 premium ANC, titanium drivers, 38h battery.",
     [("Mau sac", ["Den", "Xam"])]),

    # --- Loa (more) ---
    ("loa", "JBL PartyBox 310", "JBL", "My", 7990000, 10, 60,
     "JBL PartyBox 310 240W, light show, 18h battery.",
     [("Mau sac", ["Den"])]),

    ("loa", "JBL PartyBox 110", "JBL", "My", 4490000, 12, 80,
     "JBL PartyBox 110 160W, light show, IPX4.",
     [("Mau sac", ["Den", "Xanh"])]),

    ("loa", "Sony LSPX-S3", "Sony", "Nhat Ban", 3990000, 8, 50,
     "Sony LSPX-S3 glass tube speaker, ambient light.",
     [("Mau sac", ["Den"])]),

    ("loa", "UE Boom 4", "Ultimate Ears", "My", 3990000, 10, 70,
     "UE Boom 4 360° sound, 15h battery, IP67 waterproof.",
     [("Mau sac", ["Den", "Xanh", "Do", "Trang"])]),

    ("loa", "Sonos Era 100", "Sonos", "My", 5990000, 5, 40,
     "Sonos Era 100 stereo speaker, Alexa built-in.",
     [("Mau sac", ["Den", "Trang"])]),

    ("loa", "Anker Soundcore Motion+", "Anker", "Trung Quoc", 1990000, 15, 150,
     "Motion+ Hi-Res Audio, 30W, 12h battery.",
     [("Mau sac", ["Den"])]),

    # --- Dong ho thong minh (more) ---
    ("dong-ho-thong-minh", "Apple Watch Ultra 2", "Apple", "My", 17990000, 5, 40,
     "Apple Watch Ultra 2 49mm, 36h battery, titanium.",
     [("Mau sac", ["Den", "Trang"])]),

    ("dong-ho-thong-minh", "Samsung Galaxy Watch Ultra", "Samsung", "Han Quoc", 14990000, 8, 35,
     "Galaxy Watch Ultra 47mm, 100h battery, titanium.",
     [("Mau sac", ["Xam", "Trang"])]),

    ("dong-ho-thong-minh", "Google Pixel Watch 2", "Google", "My", 7990000, 10, 50,
     "Pixel Watch 2 Fitbit health, 24h battery, LTE.",
     [("Mau sac", ["Den", "Trang", "Xam"])]),

    ("dong-ho-thong-minh", "Amazfit GTR 4", "Amazfit", "Trung Quoc", 2990000, 15, 200,
     "GTR 4 14 days battery, dual-band GPS, 150+ sports.",
     [("Mau sac", ["Den", "Xam", "Trang"])]),

    ("dong-ho-thong-minh", "Amazfit GTS 4", "Amazfit", "Trung Quoc", 2590000, 15, 250,
     "GTS 4 slim design, 14 days battery, Alexa.",
     [("Mau sac", ["Den", "Vang", "Trang", "Xanh"])]),

    ("dong-ho-thong-minh", "Coros Apex 2 Pro", "Coros", "Trung Quoc", 8990000, 5, 30,
     "Apex 2 Pro multisport, 45 days battery, dual GPS.",
     [("Mau sac", ["Den", "Xam"])]),

    ("dong-ho-thong-minh", "Suunto Race", "Suunto", "Phan Lan", 12990000, 0, 20,
     "Suunto Race AMOLED, 26h GPS, titanium.",
     [("Mau sac", ["Den", "Trang"])]),

    # --- My pham (more) ---
    ("cham-soc-da-mat", "Tinh chat Estee Lauder Advanced Night Repair", "Estee Lauder", "My", 2100000, 10, 80,
     "Estee Lauder ANR serum 30ml, repairing, hydrating.",
     [("Mau sac", ["Trang"])]),

    ("cham-soc-da-mat", "Kem duong SK-II Facial Treatment Essence", "SK-II", "Nhat Ban", 1650000, 5, 60,
     "SK-II Pitera essence 230ml, brightening, anti-aging.",
     [("Mau sac", ["Trang"])]),

    ("cham-soc-da-mat", "Kem chong nang Shiseido Ultimate Sun Defense", "Shiseido", "Nhat Ban", 890000, 8, 120,
     "Shiseido SPF50+ PA++++, wet skin application.",
     [("Mau sac", ["Trang"])]),

    ("cham-soc-da-mat", "Tay trang Garnier Micellar Water", "Garnier", "Phap", 95000, 0, 500,
     "Garnier micellar water 400ml, gentle makeup remover.",
     [("Mau sac", ["Xanh", "Hong"])]),

    ("cham-soc-da-mat", "Kem duong Laneige Cream Skin", "Laneige", "Han Quoc", 450000, 10, 150,
     "Laneige Cream Skin 150ml, milky moisturizer.",
     [("Mau sac", ["Trang"])]),

    ("cham-soc-da-mat", "Serum The Ordinary Niacinamide 10%", "The Ordinary", "Canada", 220000, 0, 400,
     "Niacinamide 10% + Zinc 1%, oil control, pores.",
     [("Mau sac", ["Trang"])]),

    ("cham-soc-da-mat", "Retinol La Roche-Posay", "La Roche-Posay", "Phap", 650000, 8, 180,
     "La Roche-Posay Retinol B3 serum, anti-aging.",
     [("Mau sac", ["Trang"])]),

    ("trang-diem", "Phan nền Fenty Beauty Pro Filt'r", "Fenty Beauty", "My", 850000, 10, 200,
     "Fenty Pro Filt'r foundation 40 shades.",
     [("Mau sac", ["Trang", "Bac", "Vang", "Den"])]),

    ("trang-diem", "Son YSL Rouge Pur Couture", "YSL", "Phap", 890000, 5, 100,
     "YSL Rouge Pur Couture lipstick, velvet finish.",
     [("Mau sac", ["Do", "Hong", "Tim", "Cam"])]),

    ("trang-diem", "Phan ma hong NARS Orgasm", "NARS", "My", 650000, 8, 120,
     "NARS Orgasm blush, iconic peachy pink.",
     [("Mau sac", ["Hong", "Cam", "Vang"])]),

    ("trang-diem", "Kate Somerville Concealer", "Kate Somerville", "My", 590000, 10, 150,
     "Kate Somerville Concealer Katebiotic, full coverage.",
     [("Mau sac", ["Trang", "Bac", "Vang"])]),

    ("trang-diem", "Phan phu Hourglass Ambient Lighting", "Hourglass", "My", 1450000, 5, 50,
     "Hourglass Ambient Lighting Powder, soft focus.",
     [("Mau sac", ["Trang", "Vang", "Xam"])]),

    ("nuoc-hoa", "Tom Ford Black Orchid EDP", "Tom Ford", "My", 4500000, 0, 25,
     "Tom Ford Black Orchid luxurious, dark floral.",
     [("Mau sac", ["Den"])]),

    ("nuoc-hoa", "Jo Malone London English Pear", "Jo Malone", "Anh", 2800000, 10, 50,
     "Jo Malone English Pear & Freesia, fresh, fruity.",
     [("Mau sac", ["Vang"])]),

    ("nuoc-hoa", "Maison Margiela Replica Jazz Club", "Maison Margiela", "Phap", 3200000, 8, 40,
     "Jazz Club rum, tobacco, vanilla.",
     [("Mau sac", ["Nau"])]),

    ("nuoc-hoa", "Byredo Gypsy Water", "Byredo", "Thuỵ Điển", 3800000, 5, 30,
     "Gypsy Water pine, incense, lemon.",
     [("Mau sac", ["Trang"])]),

    # --- Thoi trang (more) ---
    ("ao", "Ao khoac North Face 1996 Retro Nuptse", "The North Face", "My", 3290000, 8, 80,
     "1996 Nuptse puffy, 700-fill down, water resistant.",
     [("Mau sac", ["Den", "Xanh", "Vang", "Do"]), ("Size", ["XS", "S", "M", "L", "XL"])]),

    ("ao", "Ao khoac Patagonia Nano Puff", "Patagonia", "My", 2490000, 10, 100,
     "Patagonia Nano Puff lightweight, PrimaLoft insulation.",
     [("Mau sac", ["Den", "Xanh", "Cam", "Trang"]), ("Size", ["XS", "S", "M", "L", "XL"])]),

    ("ao", "Ao len Cashmere", "Loro Piana", "Y", 15990000, 0, 20,
     "Loro Piana cashmere sweater, Italian craftsmanship.",
     [("Mau sac", ["Be", "Xam", "Den"]), ("Size", ["S", "M", "L", "XL"])]),

    ("quan", "Quan du jeans", "Levi's", "My", 1790000, 10, 150,
     "Levi's 501 original fit, 100% cotton denim.",
     [("Mau sac", ["Den", "Xanh"]), ("Size", ["28", "30", "32", "34", "36"])]),

    ("quan", "Quan jogger Nike", "Nike", "My", 790000, 12, 200,
     "Nike Jogger fleece, comfortable, casual.",
     [("Mau sac", ["Den", "Xam", "Xanh Navy"]), ("Size", ["S", "M", "L", "XL", "XXL"])]),

    ("giay-dep", "Giay Nike Dunk Low", "Nike", "My", 2490000, 10, 200,
     "Nike Dunk Low retro basketball, leather upper.",
     [("Mau sac", ["Trang", "Den", "Xanh", "Hong"]), ("Size giay", ["38", "39", "40", "41", "42", "43", "44"])]),

    ("giay-dep", "Giay New Balance 550", "New Balance", "My", 2190000, 8, 180,
     "NB 550 basketball inspired, leather, retro style.",
     [("Mau sac", ["Trang", "Den", "Xanh"]), ("Size giay", ["38", "39", "40", "41", "42", "43", "44"])]),

    ("giay-dep", "Giay Vans Old Skool", "Vans", "My", 1290000, 5, 300,
     "Vans Old Skool classic skate shoe, canvas/suede.",
     [("Mau sac", ["Den", "Trang", "Do", "Xanh"]), ("Size giay", ["36", "37", "38", "39", "40", "41", "42", "43"])]),

    ("giay-dep", "Giay Puma RS-X", "Puma", "Duc", 2190000, 12, 150,
     "Puma RS-X bold design, comfortable cushioning.",
     [("Mau sac", ["Trang", "Den", "Xanh", "Do"]), ("Size giay", ["38", "39", "40", "41", "42", "43", "44"])]),

    ("tui-xach", "Tui xach Louis Vuitton Neverfull", "Louis Vuitton", "Phap", 18990000, 0, 15,
     "LV Neverfull MM monogram canvas, iconic tote.",
     [("Mau sac", ["Nau", "Trang", "Den"])]),

    ("tui-xach", "Tui xach Gucci Marmont", "Gucci", "Y", 12990000, 5, 25,
     "Gucci Marmont small shoulder bag, chevron leather.",
     [("Mau sac", ["Den", "Vang", "Hong"])]),

    ("tui-xach", "Balo Herschel Supply Co", "Herschel", "Canada", 890000, 10, 250,
     "Herschel Classic backpack, 25L, laptop 15 inch.",
     [("Mau sac", ["Den", "Xanh", "Do", "Xam"])]),

    # --- Do the thao (more) ---
    ("do-the-thao", "Vot Pickleball Selkirk", "Selkirk", "My", 1290000, 8, 80,
     "Selkirk paddle graphite, control, power.",
     [("Mau sac", ["Xanh", "Do", "Tim"])]),

    ("do-the-thao", "Bong tennis Wilson Pro Staff", "Wilson", "My", 450000, 5, 150,
     "Wilson Pro Staff v13, classic feel, control.",
     [("Mau sac", ["Xanh", "Den"])]),

    ("do-the-thao", "Bong bida Predator", "Predator", "My", 890000, 10, 100,
     "Predator pool cue maple, pro taper.",
     [("Mau sac", ["Den", "Nau"])]),

    # --- Thuc pham (more) ---
    ("thuc-pham-chuc-nang", "Pre-workout C4", "Cellucor", "My", 550000, 10, 300,
     "C4 Original pre-workout, energy, focus.",
     [("Mau sac", ["Xanh", "Do", "Tim"])]),

    ("thuc-pham-chuc-nang", "BCAA Optimum Nutrition", "Optimum Nutrition", "My", 450000, 8, 250,
     "ON BCAA 2:1:1, muscle recovery, 30 servings.",
     [("Mau sac", ["Xanh", "Do"])]),

    ("thuc-pham-chuc-nang", "Creatine Monohydrate", "Optimum Nutrition", "My", 380000, 5, 400,
     "ON Creatine 5g, strength, power.",
     [("Mau sac", ["Trang"])]),

    ("do-an-vat", "Snack khoai tây Kettle Brand", "Kettle Brand", "My", 65000, 0, 500,
     "Kettle Brand chips, kettle cooked, sea salt.",
     [("Mau sac", ["Vang"])]),

    ("do-an-vat", "Hạt hướng dương Planters", "Planters", "My", 55000, 0, 400,
     "Planters sunflower seeds, roasted, salted.",
     [("Mau sac", ["Nau"])]),

    ("do-uong", "Cà phê Starbucks Via", "Starbucks", "My", 125000, 0, 600,
     "Starbucks VIA instant coffee, Pike Place.",
     [("Mau sac", ["Nau"])]),

    ("do-uong", "Trà xanh Matcha Ippodo", "Ippodo", "Nhat Ban", 450000, 5, 200,
     "Ippodo matcha ceremonial grade, Japan.",
     [("Mau sac", ["Xanh"])]),

    # --- Gia dung (more) ---
    ("do-gia-dung", "Robot hut bui iRobot Roomba", "iRobot", "My", 11990000, 8, 40,
     "iRobot Roomba j7+ self-emptying, mapping, Alexa.",
     [("Mau sac", ["Xam"])]),

    ("do-gia-dung", "May say qua Xiaomi", "Xiaomi", "Trung Quoc", 1490000, 12, 100,
     "Xiaomi fruit dryer 12L, low temperature.",
     [("Mau sac", ["Trang"])]),

    ("do-gia-dung", "Binh nuoc nong lọc Xiaomi", "Xiaomi", "Trung Quoc", 2990000, 10, 60,
     "Xiaomi water dispenser filtered, instant hot.",
     [("Mau sac", ["Trang"])]),

    ("do-gia-dung", "May pha ca phe Philips 5400", "Philips", "Ha Lan", 8990000, 8, 40,
     "Philips 5400 fully automatic, LatteGo.",
     [("Mau sac", ["Den"])]),

    ("do-gia-dung", "May say toc Dyson's Airwrap", "Dyson", "Anh", 14990000, 5, 25,
     "Dyson Airwrap multi-styler, coanda effect.",
     [("Mau sac", ["Trang", "Hong", "Nau"])]),

    ("do-gia-dung", "May xoa rang Electrolux", "Electrolux", "Thụy Điển", 2990000, 8, 50,
     "Electrolux air fryer 6L, RapidAir.",
     [("Mau sac", ["Den", "Trang"])]),

    # --- Game (more) ---
    ("game-pc", "Tai nghe gaming Razer BlackShark V2", "Razer", "My", 2490000, 10, 100,
     "Razer BlackShark V2 THX spatial, titanium drivers.",
     [("Mau sac", ["Den", "Xanh"])]),

    ("game-pc", "Ban phim co Logitech G915 TKL", "Logitech", "My", 4990000, 8, 40,
     "G915 TKL wireless mechanical, GL switches.",
     [("Mau sac", ["Den", "Trang"])]),

    ("game-pc", "Chuot gaming Razer Viper V3 Pro", "Razer", "My", 2190000, 10, 80,
     "Viper V3 Pro 57g, 35K DPI optical switches.",
     [("Mau sac", ["Den", "Trang"])]),

    ("game-pc", "Man hinh cong gaming Samsung Odyssey G9", "Samsung", "Han Quoc", 24990000, 5, 20,
     "Samsung Odyssey G9 49 inch DQHD 240Hz, curved.",
     [("Mau sac", ["Den"])]),

    ("game-pc", "Man hinh cong gaming LG UltraGear 27", "LG", "Han Quoc", 8990000, 10, 50,
     "LG UltraGear 27GP950 4K 144Hz, Nano IPS.",
     [("Mau sac", ["Den"])]),

    ("game-console", "Tai nghe PS5 Pulse Elite", "Sony", "Nhat Ban", 1990000, 8, 60,
     "PS5 Pulse Elite wireless, 3D audio.",
     [("Mau sac", ["Trang"])]),

    ("game-console", " Tay cầm PS5 DualSense Edge", "Sony", "Nhat Ban", 2490000, 5, 40,
     "DualSense Edge pro controller, back buttons.",
     [("Mau sac", ["Den"])]),

    # --- Camera (more) ---
    ("may-anh", "GoPro Hero 13 Black", "GoPro", "My", 12990000, 8, 50,
     "GoPro Hero 13 Black 5.3K, HyperSmooth 6.0, HB lens.",
     [("Mau sac", ["Den"])]),

    ("may-anh", "DJI Pocket 3", "DJI", "Trung Quoc", 8990000, 10, 40,
     "DJI Pocket 3 4K 120fps, 3-axis gimbal.",
     [("Mau sac", ["Den"])]),

    # --- Sach (more) ---
    ("sach", "Sách Đời Đẹp Để Sống", "NXB Trẻ", "Viet Nam", 89000, 0, 300,
     "Đời đẹp để sống - sách triết lý sống.",
     [("Mau sac", ["Xanh"])]),

    ("sach", "Sách Nghệ Thuật Nói Không", "First News", "Viet Nam", 95000, 0, 400,
     "Nghệ thuật nói không - kỹ năng giao tiếp.",
     [("Mau sac", ["Do"])]),

    ("sach", "Sách Sống Một Đời Bình Yên", "NXB Hồng Đức", "Viet Nam", 79000, 0, 350,
     "Sống một đời bình yên - triết lý Zen.",
     [("Mau sac", ["Vang"])]),

    ("van-phong-pham", "Bút máy Pilot Namiki", "Pilot", "Nhat Ban", 2500000, 0, 30,
     "Pilot Namiki fountain pen, 18K gold nib.",
     [("Mau sac", ["Den", "Vang"])]),

    ("van-phong-pham", "Đồng hồ báo thức Casio", "Casio", "Nhat Ban", 350000, 0, 200,
     "Casio alarm clock retro design.",
     [("Mau sac", ["Den", "Trang", "Xam"])]),

    # --- Phu kien dien thoai (more) ---
    ("phu-kien-dien-thoai", "Oppo Air Glass 3", "OPPO", "Trung Quoc", 8990000, 10, 40,
     "OPPO Air Glass 3 AR glasses, voice assistant.",
     [("Mau sac", ["Trang"])]),

    ("phu-kien-dien-thoai", "Samsung Galaxy Ring", "Samsung", "Han Quoc", 6990000, 8, 50,
     "Samsung Galaxy Ring health tracking, titanium.",
     [("Mau sac", ["Den", "Vang", "Trang"])]),

    ("phu-kien-dien-thoai", "Belkin MagSafe charger", "Belkin", "My", 890000, 10, 200,
     "Belkin 3-in-1 MagSafe charger for Apple devices.",
     [("Mau sac", ["Trang"])]),

    ("phu-kien-dien-thoai", "Anker 737 Power Bank", "Anker", "Trung Quoc", 1590000, 12, 150,
     "Anker 737 24,000mAh 140W, display.",
     [("Mau sac", ["Den"])]),

    # --- Phu kien may tinh (more) ---
    ("phu-kien-may-tinh", "Man hinh Dell UltraSharp 27", "Dell", "My", 8990000, 8, 40,
     "Dell U2723QE 27 inch 4K IPS Black, USB-C hub.",
     [("Mau sac", ["Den"])]),

    ("phu-kien-may-tinh", "Chuot Logitech MX Master 3S", "Logitech", "My", 1990000, 10, 100,
     "MX Master 3S 8K DPI, quiet clicks, Flow.",
     [("Mau sac", ["Den", "Trang", "Xam"])]),

    ("phu-kien-may-tinh", "Ban phim co Keychron Q1 Pro", "Keychron", "Trung Quoc", 2490000, 8, 60,
     "Keychron Q1 Pro wireless mechanical, hot-swappable.",
     [("Mau sac", ["Xam", "Trang"])]),

    ("phu-kien-may-tinh", "Tai nghe Logitech Zone Vibe 100", "Logitech", "My", 1490000, 12, 120,
     "Logitech Zone Vibe 100 wireless, lightweight.",
     [("Mau sac", ["Den", "Trang", "Xanh"])]),

    # --- Do choi (more) ---
    ("do-choi", "Nintendo Switch Sports", "Nintendo", "Nhat Ban", 1490000, 5, 80,
     "NS Sports motion controls, 6 sports.",
     [("Mau sac", ["Trang"])]),

    ("do-choi", "Mario Kart 8 Deluxe", "Nintendo", "Nhat Ban", 1190000, 0, 100,
     "Mario Kart 8 Deluxe 48 racers, battle mode.",
     [("Mau sac", ["Nhiều màu"])]),

    # --- Do cu (more) ---
    ("do-thu-cuoi", "Váy cưới đuôi cá", "Vera Wang", "My", 45990000, 0, 10,
     "Vera Wang princess ballgown, lace, beaded.",
     [("Mau sac", ["Trắng", "Kem", "Bạc"])]),

    ("do-thu-cuoi", "Áo cưới nam", "Hugo Boss", "Đức", 12990000, 0, 20,
     "Hugo Boss tuxedo slim fit, wool blend.",
     [("Mau sac", ["Đen", "Xám"])]),

    # --- Noi that (more) ---
    ("noi-that", "Ghế gaming Herman Miller", "Herman Miller", "My", 18990000, 0, 15,
     "Herman Miller Embody gaming chair, ergonomic.",
     [("Mau sac", ["Đen", "Xám"])]),

    ("noi-that", "Bàn làm việc Jarvis", "Fully", "My", 8990000, 5, 25,
     "Jarvis standing desk bamboo, electric adjustable.",
     [("Mau sac", ["Gỗ", "Trắng", "Đen"])]),

    # --- Do trang tri (more) ---
    ("do-trang-tri", "Kệ sách IKEA KALLAX", "IKEA", "Thụy Điển", 1490000, 0, 100,
     "IKEA KALLAX 4x4 shelving, multiple colors.",
     [("Mau sac", ["Trắng", "Đen", "Gỗ"])]),

    ("do-trang-tri", "Đèn LED Xiaomi Smart", "Xiaomi", "Trung Quoc", 990000, 15, 200,
     "Xiaomi smart LED strip 2m, RGB, app control.",
     [("Mau sac", ["Nhiều màu"])]),
]

_SKU_COUNTER = [0]
def _make_sku():
    _SKU_COUNTER[0] += 1
    return f"SKU{_SKU_COUNTER[0]:05d}"

FAQ_TEMPLATES = [
    ("San pham co bao hanh khong?",
     "San pham duoc bao hanh {months} thang chinh hang. Mang theo hoa don khi yeu cau bao hanh."),
    ("Co ho tro doi tra khong?",
     "Ho tro doi tra trong 7 ngay neu san pham co loi tu nha san xuat, con nguyen tem hop."),
    ("Giao hang mat bao lau?",
     "Noi thanh 1-2 ngay. Tinh thanh khac 3-5 ngay lam viec. Co giao hoa toc trong ngay."),
    ("Co ho tro tra gop khong?",
     "Ho tro tra gop 0% lai suat qua the tin dung Visa/Mastercard, toi thieu 3 thang."),
    ("Hang co chinh hang khong?",
     "100% hang chinh hang, nhap khau chinh ngach, co tem phu tieng Viet."),
    ("Co freeship khong?",
     "Mien phi van chuyen cho don tu 500.000d hoac dung ma SHIP0 khi thanh toan."),
    ("Thanh toan bang gi?",
     "Chap nhan COD, chuyen khoan, MoMo, VNPay, ZaloPay. Tra gop 0% qua the tin dung."),
    ("Co the xem hang truoc khi mua khong?",
     "Quy khach co the xem hang tai showroom hoac tra lai neu hang khong dung mo ta."),
]

def _seed_products(session, cats, tags, attrs):
    print(f"  Products ({len(PRODUCT_DATA)})...")
    products = []
    tag_list = list(tags.values())

    attr_map   = {name: (a, avs) for name, (a, avs) in attrs.items()}
    av_lookup  = {name: {av.value: av for av in avs} for name, (a, avs) in attrs.items()}

    def cartesian(lists):
        if not lists:
            return [()]
        result = []
        for rest in cartesian(lists[1:]):
            for item in lists[0]:
                result.append((item,) + rest)
        return result

    for idx, (cat_slug, name, brand, origin,
              base_price, sale_pct, stock,
              description, variants_config) in enumerate(PRODUCT_DATA):

        cat = cats.get(cat_slug)
        if not cat:
            continue
        slug = slugify(name) + f"-{idx+1}"

        p = Product(
            name=name, slug=slug, brand=brand, origin=origin,
            category_id=cat.id,
            short_description=description[:120],
            description=description,
            is_featured=(idx % 7 == 0), is_active=True,
            view_count=random.randint(50, 80000),
            avg_rating=round(random.uniform(3.4, 5.0), 2),
            review_count=random.randint(3, 500),
            created_at=rand_date(400), updated_at=datetime.now()
        )
        session.add(p); session.flush()

        for tg in random.sample(tag_list, random.randint(2, 4)):
            session.add(ProductTag(product_id=p.id, tag_id=tg.id))

        for img_i in range(random.randint(2, 5)):
            session.add(ProductImage(
                product_id=p.id,
                image_path=f"/images/products/{slug}/{img_i+1}.jpg",
                is_primary=(img_i == 0), order=img_i,
                created_at=rand_date(300), updated_at=datetime.now()
            ))

        for fi, (q, a_tmpl) in enumerate(random.sample(FAQ_TEMPLATES, random.randint(2, 4))):
            session.add(ProductFAQ(
                product_id=p.id, question=q,
                answer=a_tmpl.format(months=random.choice([6, 12, 18, 24])),
                order=fi, created_at=rand_date(300), updated_at=datetime.now()
            ))

        combo_lists = []
        for attr_name, values in variants_config:
            lkp = av_lookup.get(attr_name, {})
            combo_lists.append([(attr_name, lkp[v]) for v in values if v in lkp])

        combos = cartesian(combo_lists) if combo_lists else [()]

        for vi, combo in enumerate(combos):
            price = Decimal(base_price) * Decimal(str(round(random.uniform(0.92, 1.08), 4)))
            price = Decimal(round(float(price) / 1000) * 1000)
            sale_price = None
            if sale_pct > 0 and random.random() > 0.25:
                sale_price = Decimal(round(float(price) * (1 - sale_pct / 100) / 1000) * 1000)

            v = ProductVariant(
                product_id=p.id, sku=_make_sku(),
                price=price, sale_price=sale_price,
                stock_quantity=max(0, stock + random.randint(-20, 20)),
                alert_quantity=10,
                weight=Decimal(str(round(random.uniform(0.05, 4.0), 2))),
                is_default=(vi == 0), is_active=True, order=vi,
                created_at=rand_date(300), updated_at=datetime.now()
            )
            session.add(v); session.flush()

            for attr_name, av_obj in combo:
                a_obj, _ = attr_map[attr_name]
                session.add(ProductVariantAttribute(
                    variant_id=v.id,
                    attribute_id=a_obj.id,
                    attribute_value_id=av_obj.id,
                    created_at=rand_date(300), updated_at=datetime.now()
                ))

        products.append(p)

    session.flush()
    print(f"     -> {len(products)} products seeded.")
    return products


# ── Coupons ───────────────────────────────────────────────────────────────────
# (code, name, type, value, max_disc, min_order, limit, used, is_public, is_active, days_ago_start, days_fwd_end)

COUPON_DATA = [
    ("WELCOME10", "Chao mung khach moi - Giam 10%",      "percentage",    10,     100000, 200000, 500,  120, True,  True,  180, 180),
    ("SUMMER20",  "Sale He 2025 - Giam 20%",             "percentage",    20,     200000, 300000, 200,  88,  True,  True,  60,  60),
    ("FLASH50K",  "Flash Sale - Giam 50.000d",           "fixed",         50000,  None,   150000, 100,  55,  True,  True,  30,  30),
    ("SHIP0",     "Mien phi van chuyen toan quoc",       "free_shipping", 0,      None,   100000, None, 230, True,  True,  90,  90),
    ("VIP15",     "Uu dai VIP - Giam 15%",               "percentage",    15,     300000, 500000, 100,  40,  False, True,  120, 120),
    ("NEWPHONE",  "Mua dien thoai moi - Giam 500k",      "fixed",         500000, None,   5000000, 50,  12,  True,  True,  60,  45),
    ("TECH5",     "Tech Fest - Giam 5%",                 "percentage",    5,      150000, 2000000, 300, 175, True,  True,  90,  30),
    ("BIRTHDAY",  "Sinh nhat shop - Giam 30%",           "percentage",    30,     500000, 1000000, 50,  22,  True,  True,  14,  14),
    ("LOYAL100K", "Doi diem - Giam 100k",                "fixed",         100000, None,   0,      None, 89,  False, True,  365, 90),
    ("FREESHIP2", "Free ship don thu 2",                 "free_shipping", 0,      None,   200000, 200,  60,  True,  True,  45,  45),
    ("EXPIRED25", "Khuyen mai cu het han",               "percentage",    25,     200000, 500000, 100,  100, True,  False, 365, 0),
    ("FASHION15", "Thoi trang mua moi 15%",              "percentage",    15,     250000, 400000, 150,  30,  True,  True,  30,  60),
    ("BEAUTY10",  "My pham & Lam dep - Giam 10%",        "percentage",    10,     100000, 250000, 200,  45,  True,  True,  60,  60),
    ("FOOD5",     "Thuc pham suc khoe giam 5%",          "percentage",    5,      50000,  100000, 500,  200, True,  True,  90,  90),
    ("MEGA500K",  "Sieu sale - Giam 500k don tu 5 trieu","fixed",         500000, None,   5000000, 30,  8,   True,  True,  7,   7),
    ("NEWUSER20K","Tang 20k cho dang ky moi",            "fixed",         20000,  None,   50000,  1000, 310, True,  True,  200, 100),
    ("SHOPEE10",  "Ket hop Shopee giam them 10%",        "percentage",    10,     80000,  300000, 300,  90,  True,  True,  30,  30),
    ("APP15K",    "Dat qua App - Giam 15k",              "fixed",         15000,  None,   100000, None, 410, True,  True,  180, 90),
    ("LAPTOP5",   "Mua laptop giam them 5%",             "percentage",    5,      500000, 10000000, 80, 15,  True,  True,  30,  30),
    ("EARLYBIRD", "Early Bird - 25% doi khach hang dau", "percentage",    25,     300000, 500000,  30,  30,  False, True,  365, 30),
    ("GAME10", "Gaming Gear - Giam 10%", "percentage", 10, 200000, 300000, 100, 25, True, True, 60, 60),
    ("SPORTS20", "The thao - Giam 20%", "percentage", 20, 150000, 500000, 80, 15, True, True, 45, 45),
    ("BOOK15", "Sach van phong pham - Giam 15%", "percentage", 15, 50000, 200000, 150, 40, True, True, 90, 90),
    ("CAMPING30", "Camping - Giam 30%", "percentage", 30, 200000, 1000000, 30, 8, True, True, 30, 30),
    ("VALI10", "Vali ba lo - Giam 10%", "percentage", 10, 100000, 500000, 100, 30, True, True, 60, 60),
    ("PHONE25", "Dien thoai - Giam 25%", "percentage", 25, 500000, 3000000, 50, 10, True, True, 14, 14),
    ("WATCH10", "Dong ho - Giam 10%", "percentage", 10, 150000, 400000, 80, 20, True, True, 60, 60),
    ("AUDIO20", "Am thanh - Giam 20%", "percentage", 20, 200000, 500000, 60, 12, True, True, 45, 45),
    ("COSMETIC15", "My pham - Giam 15%", "percentage", 15, 100000, 300000, 120, 35, True, True, 60, 60),
    ("FRAGRANCE10", "Nuoc hoa - Giam 10%", "percentage", 10, 200000, 800000, 50, 18, True, True, 90, 90),
    ("FASHION25", "Thoi trang - Giam 25%", "percentage", 25, 200000, 600000, 100, 22, True, True, 30, 30),
    ("SHOES15", "Giay dep - Giam 15%", "percentage", 15, 100000, 400000, 150, 45, True, True, 60, 60),
    ("BAG10", "Tui xach - Giam 10%", "percentage", 10, 150000, 500000, 80, 28, True, True, 60, 60),
    ("CAMERA20", "May anh - Giam 20%", "percentage", 20, 500000, 2000000, 30, 5, True, True, 30, 30),
    ("CONSOLE15", "Game console - Giam 15%", "percentage", 15, 300000, 1500000, 40, 8, True, True, 30, 30),
    ("TOY10", "Do choi - Giam 10%", "percentage", 10, 80000, 300000, 200, 60, True, True, 90, 90),
    ("PET10", "San pham thu cung - Giam 10%", "percentage", 10, 100000, 400000, 100, 30, True, True, 60, 60),
    ("AUTO20", "Phu kien o to - Giam 20%", "percentage", 20, 200000, 800000, 60, 15, True, True, 60, 60),
    ("BIKE15", "Phu kien xe may - Giam 15%", "percentage", 15, 150000, 500000, 80, 25, True, True, 60, 60),
    ("HOME25", "Gia dung - Giam 25%", "percentage", 25, 200000, 1000000, 70, 18, True, True, 45, 45),
    ("FURNITURE20", "Noi that - Giam 20%", "percentage", 20, 500000, 3000000, 40, 10, True, True, 60, 60),
    ("LIGHT10", "Den trang tri - Giam 10%", "percentage", 10, 100000, 400000, 90, 35, True, True, 90, 90),
    ("DRINK10", "Do uong - Giam 10%", "percentage", 10, 50000, 200000, 300, 120, True, True, 90, 90),
    ("SUPPER50K", "Qua tang - Giam 50k", "fixed", 50000, None, 200000, 150, 55, True, True, 60, 60),
    ("FIRSTORDER", "Don hang dau tien - Giam 30%", "percentage", 30, 300000, 500000, 500, 200, True, True, 365, 180),
    ("MEMBER15", "Thanh vien - Giam 15%", "percentage", 15, 200000, 400000, 200, 80, False, True, 365, 90),
    ("FLASHDEAL", "Flash Deal - Giam 40%", "percentage", 40, 400000, 2000000, 25, 5, True, True, 7, 7),
    ("WEEKSALE", "Sale cuoi tuan - Giam 25%", "percentage", 25, 250000, 800000, 60, 20, True, True, 14, 7),
    ("MONTHLY15", "Hang thang - Giam 15%", "percentage", 15, 150000, 500000, 100, 45, True, True, 30, 30),
]

def _seed_coupons(session):
    print(f"  Coupons ({len(COUPON_DATA)})...")
    coupons = []
    for (code, name, ctype, value, max_disc, min_order,
         limit, used, is_public, is_active,
         days_ago_start, days_fwd_end) in COUPON_DATA:
        end_date = (datetime.now() - timedelta(days=30) if days_fwd_end == 0
                    else datetime.now() + timedelta(days=days_fwd_end))
        c = Coupon(
            code=code, name=name, description=name,
            type=ctype,
            value=Decimal(value),
            max_discount=Decimal(max_disc) if max_disc else None,
            min_order_value=Decimal(min_order) if min_order else Decimal(0),
            usage_limit=limit, usage_per_user=2,
            used_count=used, points_required=0,
            applicable_to="all",
            start_date=datetime.now() - timedelta(days=days_ago_start),
            end_date=end_date,
            is_active=is_active, is_public=is_public,
            created_at=rand_date(200), updated_at=datetime.now()
        )
        session.add(c); session.flush()
        coupons.append(c)
    return coupons


# ── Orders ────────────────────────────────────────────────────────────────────

ORDER_STATUSES  = ["pending","confirmed","processing","ready_to_ship","shipping","delivered","completed","cancelled","refunding","refunded","returned"]
STATUS_WEIGHTS  = [5, 8, 8, 6, 12, 15, 28, 8, 2, 4, 4]
PAYMENT_METHODS = ["cod","bank_transfer","momo","vnpay","zalopay"]
PAY_WEIGHTS     = [40, 20, 20, 15, 5]
CARRIERS        = ["GHN","GHTK","VNPost","J&T Express","Shopee Express","Ninja Van"]
SHIPPING_METHODS= ["Giao hang tieu chuan","Giao hang nhanh","Giao hang hoa toc"]
ORDER_NOTES     = [None, None, None,
                   "Giao gio hanh chinh", "Goi truoc khi giao",
                   "De hang truoc cua", "Giao buoi toi sau 18h",
                   "Khong bam chuong", "Giao cuoi tuan duoc khong"]
CANCEL_REASONS  = [
    "Dat nham san pham", "Tim duoc cho re hon",
    "Khong con nhu cau", "Thanh toan khong thanh cong",
    "Het hang", "Muon thay doi dia chi giao", "Cho lau qua",
    "Doi y muon san pham khac", "Mua trung voi nguoi than",
]

_ORDER_NUM = [0]
def _next_order_number():
    _ORDER_NUM[0] += 1
    return f"DH{datetime.now().strftime('%Y%m')}{_ORDER_NUM[0]:06d}"

def _seed_orders(session, users, products, coupons):
    from database.models import ProductVariant
    customers = users[3:]  # skip admin + 2 staff

    all_variants = {}
    for p in products:
        vs = session.query(ProductVariant).filter(
            ProductVariant.product_id == p.id,
            ProductVariant.is_active == True
        ).all()
        if vs:
            all_variants[p.id] = vs

    active_products = [p for p in products if p.id in all_variants]
    active_coupons  = [c for c in coupons if c.is_active]

    total_orders = 2000
    print(f"  Orders ({total_orders})...")
    orders = []

    for _ in range(total_orders):
        user       = random.choice(customers)
        status     = random.choices(ORDER_STATUSES, weights=STATUS_WEIGHTS)[0]
        pay_method = random.choices(PAYMENT_METHODS, weights=PAY_WEIGHTS)[0]
        coupon     = random.choice(active_coupons) if (random.random() < 0.28 and active_coupons) else None

        chosen    = random.sample(active_products, min(random.randint(1, 4), len(active_products)))
        order_date = rand_date(400)

        subtotal = Decimal(0)
        item_data = []
        for prod in chosen:
            variant = random.choice(all_variants[prod.id])
            qty     = random.randint(1, 3)
            price   = variant.sale_price if variant.sale_price else variant.price
            item_st = price * qty
            subtotal += item_st
            item_data.append((prod, variant, qty, price, item_st))

        discount = Decimal(0)
        if coupon and subtotal >= (coupon.min_order_value or 0):
            if coupon.type == "percentage":
                discount = subtotal * coupon.value / 100
                if coupon.max_discount:
                    discount = min(discount, coupon.max_discount)
            elif coupon.type == "fixed":
                discount = min(coupon.value, subtotal)

        shipping_fee = Decimal(0) if (coupon and coupon.type == "free_shipping") else \
                       Decimal(random.choice([0, 15000, 20000, 25000, 30000, 35000]))
        total = subtotal - discount + shipping_fee

        delivered_date = paid_at = cancelled_date = cancelled_by = cancel_reason = tracking = None
        payment_status = "pending"

        if status in ("delivered", "completed"):
            delivered_date = order_date + timedelta(days=random.randint(2, 7))
            payment_status = "paid"
            paid_at        = order_date + timedelta(hours=random.randint(1, 48))
            tracking       = rand_tracking()
        elif status == "shipping":
            tracking       = rand_tracking()
            payment_status = random.choice(["pending", "paid"])
            if payment_status == "paid":
                paid_at = order_date + timedelta(hours=1)
        elif status in ("confirmed", "processing", "ready_to_ship"):
            payment_status = random.choice(["pending", "paid"])
            if payment_status == "paid":
                paid_at = order_date + timedelta(hours=2)
        elif status in ("cancelled", "refunded", "returned", "refunding"):
            cancelled_date = order_date + timedelta(days=random.randint(1, 4))
            cancelled_by   = user.id
            cancel_reason  = random.choice(CANCEL_REASONS)
            payment_status = "refunded" if status == "refunded" else "pending"

        order = Order(
            order_number=_next_order_number(),
            user_id=user.id,
            coupon_id=coupon.id if coupon else None,
            customer_name=user.name,
            customer_email=user.email,
            customer_phone=user.phone,
            shipping_address=user.address,
            province=random.choice(PROVINCES),
            subtotal=subtotal,
            discount_amount=discount,
            shipping_fee=shipping_fee,
            tax_amount=Decimal(0),
            total=total,
            points_earned=int(float(total) // 10000),
            points_used=0,
            shipping_method=random.choice(SHIPPING_METHODS),
            shipping_carrier=random.choice(CARRIERS),
            tracking_number=tracking,
            estimated_delivery_date=order_date + timedelta(days=random.randint(2, 7)),
            actual_delivery_date=delivered_date,
            payment_method=pay_method,
            payment_status=payment_status,
            paid_at=paid_at,
            status=status,
            note=random.choice(ORDER_NOTES),
            cancel_reason=cancel_reason,
            cancelled_by=cancelled_by,
            cancelled_at=cancelled_date,
            source=random.choices(["web", "mobile"], [65, 35])[0],
            ip_address=rand_ip(),
            created_at=order_date,
            updated_at=order_date + timedelta(hours=random.randint(1, 96))
        )
        session.add(order); session.flush()

        item_status_map = {
            "pending":"pending", "confirmed":"confirmed",
            "processing":"processing", "ready_to_ship":"processing",
            "shipping":"shipped", "delivered":"delivered",
            "completed":"delivered", "cancelled":"cancelled",
            "refunding":"returned", "refunded":"refunded", "returned":"returned",
        }
        for prod, variant, qty, price, item_st in item_data:
            session.add(OrderItem(
                order_id=order.id,
                product_id=prod.id,
                variant_id=variant.id,
                product_name=prod.name,
                sku=variant.sku,
                variant_attributes={},
                price=price, quantity=qty,
                discount_amount=Decimal(0),
                subtotal=item_st,
                status=item_status_map.get(status, "pending"),
                created_at=order_date,
                updated_at=order_date + timedelta(hours=1)
            ))

        orders.append(order)

    session.flush()
    return orders


# ── Reviews ───────────────────────────────────────────────────────────────────

REVIEW_COMMENTS = [
    "San pham rat tot, dung nhu mo ta. Giao hang nhanh, dong goi can than.",
    "Chat luong on, gia hop ly. Se mua lai lan sau.",
    "Hang chinh hang, dung duoc vai tuan van tot. Shop nhiet tinh.",
    "Giao hang nhanh hon du kien. San pham dep, dung mau, dung size.",
    "Chat luong xuat sac, xung dang voi gia tien. Rat hai long!",
    "San pham ok nhung giao hoi cham, dong goi tot, khong bi hong.",
    "Dung thu thay rat on, se gioi thieu cho ban be. Cam on shop!",
    "Mua lan dau, hai long voi trai nghiem mua sam. San pham nhu hinh.",
    "Tot hon mong doi. Mau dep, chat lieu tot, dung kich thuoc.",
    "Hang dep nhung gia hoi cao. Tuy nhien chat luong bu lai.",
    "San pham dung duoc nhung khong an tuong nhu quang cao.",
    "Giao nhanh, shop phan hoi nhiet tinh, se ung ho dai dai.",
    "Chat luong tot, dung nhu description. Cam on shop tu van nhiet tinh.",
    "Mua tang nguoi than, ho rat thich. Dong goi qua rat dep.",
    "Tuyet voi! Day la lan thu 3 toi mua, lan nao cung hai long.",
    "Hang den hoi cham nhung chat luong tot, bu lai duoc.",
    "San pham dep, can doc ky mo ta truoc khi mua de khong nham size.",
    "Ok lam, dung duoc roi. Gia tot so voi thi truong.",
    "Rat ung, shop tu van nhiet tinh va giao dung hen.",
    "Bao bi chac chan, hang nguyen ven, khong bi mop meo.",
    "Mau sac dung nhu trong anh, khong bi chenh lech.",
    "Pin trau, dung duoc ca ngay ma khong lo het pin.",
    "Texture nhe, tham nhanh, khong gay mun cho da dau.",
    "Size dung nhu bang size, may vua van.",
    "Mui thom lau, khong bi bay mui sau vai gio.",
    "De giay em, di ca ngay khong moi chan.",
    "Chat lieu vai mem, khong bi nhay mau sau khi giat.",
    "Hinh thuc dep, dong goi chuan, rat hai long khi mo hop.",
    "Gia tot cho chat luong nay. So sanh voi cac shop khac rat canh tranh.",
    "Mua ve cho chong dung, anh ay rat thich. Chac chan se mua them.",
]

REVIEW_TITLES = [
    "Rat hai long!", "Tot lam!", "Chat luong xuat sac",
    "Dang tien", "Giao nhanh, hang dep", "OK lam",
    "Hai long", "Se mua lai", "Hang chinh hang",
    "Dung mo ta", "Tuyet voi", "On ap",
    "Khuyen mua", "Xung dang 5 sao", "Mua ve khong that vong",
    "San pham chuan", "Gia tot", "Dep qua di",
]

def _seed_reviews(session, users, products, orders):
    from database.models import OrderItem as OI
    reviewable = [o for o in orders if o.status in ("completed", "delivered")]
    print(f"  Reviews (from {len(reviewable)} delivered/completed orders)...")

    reviewed_pairs = set()
    count = 0

    for order in reviewable:
        if random.random() > 0.70:
            continue
        items = session.query(OI).filter(OI.order_id == order.id).all()
        for item in items:
            pair = (order.user_id, item.id)
            if pair in reviewed_pairs:
                continue
            reviewed_pairs.add(pair)
            rating = random.choices([1, 2, 3, 4, 5], weights=[2, 3, 10, 35, 50])[0]
            session.add(ProductReview(
                product_id=item.product_id,
                variant_id=item.variant_id,
                user_id=order.user_id,
                order_id=order.id,
                order_item_id=item.id,
                rating=rating,
                comment=random.choice(REVIEW_COMMENTS) if random.random() > 0.15 else None,
                is_verified_purchase=True,
                is_approved=(random.random() > 0.08),
                helpful_count=random.randint(0, 80),
                created_at=order.created_at + timedelta(days=random.randint(3, 20)),
                updated_at=datetime.now()
            ))
            count += 1

    session.flush()
    print(f"     -> {count} reviews seeded.")


# ── Chatbot ───────────────────────────────────────────────────────────────────

INTENT_DATA = [
    ("greet", "Chao hoi", "general", [
        "Xin chao", "Chao shop", "Hello", "Hi ban", "Alo shop oi",
        "Chao buoi sang", "Shop oi cho minh hoi", "Ban oi",
        "Hi shop oi", "Chao nhe", "Hey shop",
    ]),
    ("goodbye", "Tam biet", "general", [
        "Tam biet", "Bye bye", "Cam on shop nhe", "Thoi minh di",
        "Hen gap lai", "Thanks nha", "Ok tim hieu them roi quay lai",
        "Minh di truoc nhe", "Chuc ban ngay tot",
    ]),
    ("product_search", "Tim san pham", "product", [
        "Toi muon mua dien thoai", "Co ban laptop khong",
        "Tim tai nghe chong on", "Shop co ban iPhone khong",
        "Cho toi xem quan jeans", "Tim kem duong am",
        "Muon mua giay Nike", "Co ao thun Uniqlo khong",
        "Tim dong ho thong minh", "Mua loa bluetooth",
        "Co ban Samsung Galaxy S24 khong", "Cho xem san pham moi",
    ]),
    ("product_price", "Hoi gia", "product", [
        "iPhone 15 gia bao nhieu", "Gia laptop Dell la bao nhieu",
        "Tai nghe Sony bao nhieu tien", "Bao nhieu tien mot cai",
        "Co giam gia khong", "Gia goc va gia sale la bao nhieu",
        "Cho hoi gia MacBook Air M3", "San pham nay bao nhieu",
        "Gia tot nhat la bao nhieu", "Co chiet khau gi khong",
    ]),
    ("product_availability", "Con hang khong", "product", [
        "Con hang khong", "Het hang chua", "Hang ve chua",
        "iPhone 15 con hang khong", "Size M con khong",
        "Mau den con khong", "Khi nao co hang tro lai",
        "Kiem tra giup toi con hang khong", "Co san kho khong",
    ]),
    ("product_specs", "Thong so ky thuat", "product", [
        "Thong so ky thuat cua iPhone 15", "Pin bao nhieu mAh",
        "Camera bao nhieu MP", "Man hinh bao nhieu inch",
        "RAM bao nhieu GB", "Chip gi vay", "Trong luong bao nhieu",
        "Ho tro sac nhanh khong", "Co chong nuoc khong",
    ]),
    ("order_status", "Trang thai don hang", "order", [
        "Don hang cua toi dang o dau", "Don DH202501000001 the nao",
        "Khi nao giao hang", "Don hang da xac nhan chua",
        "Theo doi don hang", "Don toi dang xu ly a",
        "Bao gio nhan duoc hang", "Kiem tra don hang giup toi",
    ]),
    ("order_cancel", "Huy don", "order", [
        "Toi muon huy don", "Cho huy don DH202501000002",
        "Khong muon mua nua", "Doi y muon huy",
        "Lam sao de huy don hang", "Co the huy duoc khong",
        "Huy giup toi don nay", "Cancel don hang",
    ]),
    ("order_return", "Tra hang hoan tien", "order", [
        "Toi muon tra hang", "Hoan tien cho don cua toi",
        "Hang bi loi muon doi", "Quy trinh tra hang the nao",
        "Gui lai hang cho shop", "Doi tra san pham",
        "Hang khong dung mo ta muon tra", "Refund don hang",
    ]),
    ("promotion_current", "Khuyen mai hien tai", "promotion", [
        "Co khuyen mai gi khong", "Dang sale gi vay",
        "Cho xem uu dai hien tai", "Co deal hot khong",
        "Hom nay giam gia gi", "Flash sale luc may gio",
        "Chuong trinh khuyen mai thang nay", "Co gi dang khuyen mai",
    ]),
    ("ask_coupon", "Hoi ma giam gia", "promotion", [
        "Co ma giam gia khong", "Code voucher la gi",
        "Nhap ma o dau", "Cho xin ma khuyen mai",
        "Co ma freeship khong", "Ma WELCOME10 con khong",
        "Xin ma giam gia di", "Co voucher gi moi khong",
    ]),
    ("loyalty_points", "Diem tich luy", "account", [
        "Toi co bao nhieu diem", "Diem tich luy dung the nao",
        "Diem thuong quy doi the nao", "Co tich diem khong",
        "Hang thanh vien cua toi la gi", "Diem sap het han khong",
        "Doi diem lay gi duoc", "Huong dan tich diem",
    ]),
    ("account_info", "Thong tin tai khoan", "account", [
        "Xem thong tin tai khoan", "Doi mat khau",
        "Cap nhat dia chi", "Lich su mua hang",
        "San pham yeu thich", "Quan ly tai khoan",
    ]),
    ("shipping_info", "Thong tin van chuyen", "support", [
        "Phi ship bao nhieu", "Bao lau nhan duoc hang",
        "Ship ve tinh co duoc khong", "Giao hang mien phi khong",
        "Co giao hoa toc khong", "Don dang ship di dau",
        "Van chuyen mat may ngay", "Ship thu 7 chu nhat khong",
    ]),
    ("return_policy", "Chinh sach doi tra", "support", [
        "Chinh sach doi tra the nao", "Mua roi doi duoc khong",
        "Hang loi doi co mat phi khong", "Bao nhieu ngay duoc doi tra",
        "Quy trinh tra hang", "Dieu kien de doi tra",
        "7 ngay doi tra dung khong", "Lam sao de tra hang",
    ]),
    ("payment_method", "Phuong thuc thanh toan", "support", [
        "Thanh toan bang gi", "Co chap nhan MoMo khong",
        "Tra gop 0% khong", "Co nhan tien mat khong",
        "Thanh toan ZaloPay duoc khong", "Chuyen khoan ngan hang nao",
        "Co VNPay khong", "Thanh toan the tin dung",
    ]),
    ("product_review", "Hoi danh gia", "product", [
        "San pham nay co tot khong", "Review iPhone 15 di",
        "Ai da mua roi nhan xet the nao", "San pham co ben khong",
        "Moi nguoi danh gia sao", "Co khach mua chua",
        "Chat luong co nhu quang cao khong",
    ]),
    ("new_arrivals", "San pham moi", "product", [
        "Co san pham moi khong", "Hang moi ve chua",
        "Mau moi nhat la gi", "San pham vua ra mat",
        "Cap nhat hang moi chua", "Moi nhat la gi",
    ]),
    ("compare_products", "So sanh san pham", "product", [
        "So sanh iPhone 15 va Samsung S24", "Chon cai nao tot hon",
        "Khac biet giua 2 san pham la gi", "Nen mua cai nao",
        "iPhone va Samsung cai nao tot hon", "Giup toi chon",
    ]),
    ("ask_warranty", "Bao hanh", "support", [
        "Bao hanh bao lau", "Chinh sach bao hanh the nao",
        "Bao hanh o dau", "Sua chua nhu the nao",
        "Loi san pham bao hanh duoc khong", "Trung tam bao hanh",
    ]),
    ("payment_installment", "Tra gop", "payment", [
        "Co ho tro tra gop khong", "Tra gop 0% lai suat duoc khong",
        "Tra gop qua the tin dung", "Tra gop bao nhieu thang",
        "Toi muon mua tra gop", "Chi can tra truoc bao nhieu",
        "Lai suat tra gop la bao nhieu", "Co tra gop khong can tra truoc",
    ]),
    ("shipping_time", "Thoi gian giao hang", "shipping", [
        "Giao hang mat bao lau", "Khi nao nhan duoc hang",
        "Giao hang trong bao nhieu ngay", "Co giao hang ngay duoc khong",
        "Thoi gian giao hang noi thanh", "Thoi gian giao hang lien tinh",
        "Co giao hang cuoi tuan khong", "Giao hang nhanh trong bao lau",
    ]),
    ("shipping_areas", "Cac khu vuc giao", "shipping", [
        "Co giao den tinh nao", "Cac tinh thanh duoc giao hang",
        "Giao hang toan quoc khong", "Co giao den vung xa khong",
        "Khu vuc giao hang", "Dia chi co the giao duoc khong",
    ]),
    ("size_guide", "Huong dan chon size", "product", [
        "Size nao phu hop voi toi", "Lam sao chon size",
        "Huong dan do size", "Size S M L khac gi",
        "Bang size cua shop", "Toi mang size nao",
    ]),
    ("color_options", "Cac tuy chon mau", "product", [
        "Co mau nao khac khong", "Co bao nhieu mau",
        "Mau nao dep hon", "Mau nao pho bien",
        "Mau moi nhat", "Mau co san khong",
    ]),
    ("bulk_purchase", "Mua si", "order", [
        "Co gia si khong", "Mua nhieu co giam gia khong",
        "Gia cho dai ly", "Toi muon mua si",
        "So luong lon gia bao nhieu", "Chinh sach mua si",
    ]),
    ("gift_options", "Qua tang", "product", [
        "Co goi qua tang khong", "Co the giam gia khong",
        "Gui qua tang", "Dong goi qua tang",
        "Viet loi chuc", "Gui qua den dia chi khac",
    ]),
    ("warranty_registration", "Dang ky bao hanh", "product", [
        "Dang ky bao hanh nhu the nao", "Bao hanh tu dong khong",
        "Can dang ky bao hanh khong", "The bao hanh dien tu",
        "Cach kich hoat bao hanh", "Dang ky bao hanh online",
    ]),
    ("defective_product", "San pham loi", "order", [
        "Hang bi loi", "San pham khong hoat dong",
        "Bi vỡ khi nhan hang", "Hang khong nhu mo ta",
        "San pham khong tot", "Loi san pham",
    ]),
    ("contact_support", "Lien he ho tro", "general", [
        "Lien he shop", "Hotline la gi", "Co chat khong",
        "Ho tro qua Zalo", "Lien he qua email",
        "Dai ly o dau", "Co cua hang khong",
    ]),
    ("store_locations", "Cua hang", "general", [
        "Cua hang o dau", "Co cua hang khong",
        "Dia chi cua hang", "Cua hang gan nhat",
        "Gio mo cua", "Co the den mua truc tiep khong",
    ]),
    ("thankyou", "Cam on", "general", [
        "Cam on", "Thanks", "Thank you",
        "Cam on nhieu", "Rat cam on",
        "Thank you very much", "Cam on shop",
    ]),
    ("complaint", "Phan nan", "general", [
        "Toi muon phan nan", "Khong hai long",
        "Chat luong kem", "Phuc vu te",
        "Khong ung y", "Phan nan dich vu",
    ]),
    ("suggest_product", "Goi y san pham", "product", [
        "Goi y cho toi", "San pham nao tot",
        "Ban thich san pham nao", "San pham ban chay",
        "San pham duoc danh gia cao", "Top san pham",
    ]),
    ("faq_shipping", "Cau hoi ve giao hang", "shipping", [
        "Giao hang co an toan khong", "Co bai khong",
        "Dong goi nhu the nao", "Van chuyen co thanh khong",
        "Hang co bi hu khong", "Bao hiem hang hoa",
    ]),
    ("faq_payment", "Cau hoi ve thanh toan", "payment", [
        "Thanh toan an toan khong", "Co bi hack khong",
        "Thanh toan qua MoMo", "The tin dung co an toan",
        "Mat khau thanh toan", "Xac nhan thanh toan",
    ]),
    ("feedback", "Gop y", "general", [
        "Toi muon gop y", "Gop y cho shop",
        "Y kien khach hang", "Danh gia cua ban",
        "Gop y ve dich vu", "Phan hoi",
    ]),
]

BOT_RESPONSES = {
    "greet":             "Xin chao! Toi la tro ly mua sam cua Shop. Toi co the giup ban tim san pham, kiem tra don hang va nhieu hon nua!",
    "goodbye":           "Cam on ban da ghe tham Shop! Hen gap lai ban som nhe!",
    "product_search":    "Toi se giup ban tim san pham phu hop. Ban dang quan tam den loai san pham nao? Ngan sach ban la bao nhieu?",
    "product_price":     "De toi kiem tra gia cho ban. Ban quan tam den san pham cu the nao? Toi se tim gia tot nhat!",
    "product_availability": "Toi se kiem tra tinh trang hang ngay. Ban can san pham nao, mau/size gi?",
    "product_specs":     "Vui long cho toi biet ten san pham cu the de toi tra thong so ky thuat nhe!",
    "order_status":      "De kiem tra don hang, vui long cung cap ma don hang (bat dau bang DH) hoac email dat hang.",
    "order_cancel":      "De huy don, vui long cung cap ma don hang. Luu y chi huy duoc khi don chua duoc giao.",
    "order_return":      "De doi/tra hang: (1) Don hang trong 7 ngay, (2) Con nguyen tem hop, (3) Co hoa don. Lien he hotline de duoc ho tro!",
    "promotion_current": "Hien tai Shop dang co nhieu chuong trinh khuyen mai hap dan! Go 'xem khuyen mai' de toi liet ke chi tiet nhe!",
    "ask_coupon":        "Shop hien co nhieu ma giam gia hot! Vi du: WELCOME10 giam 10% khach moi, SHIP0 mien phi ship. Go 'xem ma giam gia' de biet them!",
    "loyalty_points":    "Tich diem: moi 100.000d = 10 diem. 100 diem = 10.000d giam gia! Hang Vang (500+ diem) giam them 10%.",
    "account_info":      "De xem thong tin tai khoan, vui long dang nhap vao website va vao muc 'Tai khoan cua toi'. Can ho tro gi khac?",
    "shipping_info":     "Phi ship tu 15.000-35.000d tuy khu vuc. Noi thanh 1-2 ngay, lien tinh 3-5 ngay. Mien phi ship don tu 500.000d!",
    "return_policy":     "Doi tra trong 7 ngay voi hang loi nha san xuat. Hang phai con nguyen tem, hop va hoa don. Lien he hotline!",
    "payment_method":    "Shop chap nhan: COD, chuyen khoan, MoMo, VNPay, ZaloPay. Tra gop 0% qua the tin dung tu 3 thang.",
    "product_review":    "San pham cua chung toi duoc danh gia rat cao! Ban muon xem danh gia san pham cu the nao?",
    "new_arrivals":      "Shop vua cap nhat nhieu san pham moi! Go 'san pham moi' de toi gioi thieu nhe!",
    "compare_products":  "Toi se giup ban so sanh! Cho toi biet ten 2 san pham ban muon so sanh nhe.",
    "ask_warranty":      "Bao hanh chinh hang 12-24 thang tuy san pham. Dem hang den cua hang hoac lien he hotline de bao hanh.",
}

def _seed_chatbot(session, users):
    customers = users[3:]

    print(f"  Chatbot: {len(INTENT_DATA)} intents...")
    intent_obj_map = {}
    for intent_name, description, category, examples in INTENT_DATA:
        ci = ChatbotIntent(
            intent_name=intent_name, description=description,
            category=category, is_active=True,
            usage_count=random.randint(20, 1200),
            created_at=rand_date(300), updated_at=datetime.now()
        )
        session.add(ci); session.flush()

        for ex in examples:
            session.add(ChatbotTrainingExample(
                intent_id=ci.id, example_text=ex, language="vi", is_active=True,
                created_at=rand_date(300), updated_at=datetime.now()
            ))

        resp_text = BOT_RESPONSES.get(intent_name, "Toi hieu yeu cau cua ban, de toi ho tro!")
        session.add(ChatbotResponse(
            intent_id=ci.id, response_text=resp_text,
            response_type="text", order=0, is_active=True,
            created_at=rand_date(300), updated_at=datetime.now()
        ))
        intent_obj_map[intent_name] = ci

    intent_pairs = list(intent_obj_map.items())

    num_convs = 500
    print(f"  Conversations ({num_convs})...")
    for ci_idx in range(num_convs):
        user      = random.choice(customers)
        conv_date = rand_date(200)
        session_id = f"sess_{user.id}_{ci_idx}_{int(conv_date.timestamp())}"

        conv = ChatbotConversation(
            user_id=user.id, session_id=session_id,
            sender_id=str(user.id),
            created_at=conv_date,
            updated_at=conv_date + timedelta(minutes=random.randint(1, 45))
        )
        session.add(conv); session.flush()

        num_turns = random.randint(2, 7)
        t = conv_date
        for turn in range(num_turns):
            intent_name, _ = random.choice(intent_pairs)
            examples_for_intent = next(x[3] for x in INTENT_DATA if x[0] == intent_name)
            user_text  = random.choice(examples_for_intent)
            confidence = round(random.uniform(0.50, 0.99), 4)

            session.add(ChatbotMessage(
                conversation_id=conv.id, sender_type="user",
                message=user_text, intent=intent_name,
                confidence=confidence, entities=None, created_at=t
            ))
            t += timedelta(seconds=random.randint(5, 120))

            bot_text = BOT_RESPONSES.get(intent_name, "Xin loi, toi chua hieu y ban. Ban co the noi ro hon khong?")
            session.add(ChatbotMessage(
                conversation_id=conv.id, sender_type="bot",
                message=bot_text, intent=intent_name,
                confidence=None, entities=None, created_at=t
            ))
            t += timedelta(seconds=random.randint(1, 10))

        if random.random() < 0.45:
            rating = random.choices([1, 2, 3, 4, 5], weights=[3, 5, 12, 35, 45])[0]
            fb_texts = {
                5: "Bot tra loi rat tot, giai quyet duoc van de cua toi!",
                4: "Kha huu ich, doi khi chua hieu dung y.",
                3: "Tam on, can cai thien them.",
                2: "Bot chua hieu cau hoi cua toi.",
                1: "Khong giup ich gi, phai nho nhan vien ho tro.",
            }
            session.add(ChatbotFeedback(
                conversation_id=conv.id, rating=rating,
                feedback_text=fb_texts[rating],
                created_at=conv_date + timedelta(minutes=random.randint(3, 90))
            ))

    session.flush()
    print(f"     -> {num_convs} conversations seeded.")


# ── entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    seed()
