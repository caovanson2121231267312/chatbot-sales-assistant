"""
Product-related Actions using SQLAlchemy ORM
Actions liên quan đến sản phẩm
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.models import (
    Product, ProductVariant, ProductCategory, ProductFAQ,
    db_session
)


class ActionSearchProducts(Action):
    """Tìm kiếm sản phẩm với ORM"""

    def name(self) -> Text:
        return "action_search_products"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        session = db_session.get_session()

        try:
            product_name = tracker.get_slot("product_name")
            product_type = tracker.get_slot("product_type")
            brand = tracker.get_slot("brand")

            # Kiểm tra nếu không có thông tin sản phẩm -> hỏi clarifying questions
            if not product_name and not product_type and not brand:
                # Lấy thông tin từ câu hỏi gốc để gợi ý
                latest_message = tracker.latest_message.get('text', '')

                # Kiểm tra xem có keyword nào trong câu hỏi không
                keywords = []
                if any(word in latest_message.lower() for word in ['laptop', 'máy tính', 'notebook', 'macbook']):
                    keywords.append('laptop')
                if any(word in latest_message.lower() for word in ['điện thoại', 'dt', 'smartphone', 'iphone', 'samsung', '手机']):
                    keywords.append('điện thoại')
                if any(word in latest_message.lower() for word in ['tai nghe', 'headphone', 'airpod']):
                    keywords.append('tai nghe')
                if any(word in latest_message.lower() for word in ['đồng hồ', 'watch', 'smartwatch']):
                    keywords.append('đồng hồ')
                if any(word in latest_message.lower() for word in ['ipad', 'tablet', 'máy tính bảng']):
                    keywords.append('máy tính bảng')

                if keywords:
                    # Có keyword nhưng không extract được entity -> gợi ý tìm kiếm
                    query = session.query(Product).join(ProductVariant).join(ProductCategory).filter(
                        Product.is_active == True,
                        ProductVariant.is_default == True
                    )

                    # Tìm theo category
                    category_map = {
                        'laptop': 'Laptop',
                        'điện thoại': 'Điện thoại',
                        'tai nghe': 'Tai nghe',
                        'đồng hồ': 'Đồng hồ',
                        'máy tính bảng': 'Tablet'
                    }

                    found_products = []
                    for kw in keywords:
                        if kw in category_map:
                            products = query.filter(
                                ProductCategory.name.like(f"%{category_map[kw]}%")
                            ).limit(3).all()
                            found_products.extend(products)

                    if found_products:
                        message = f"🔍 Tôi hiểu bạn đang tìm **{keywords[0]}**. Dưới đây là một số gợi ý:\n\n"
                        seen = set()
                        for product in found_products[:5]:
                            if product.id not in seen:
                                seen.add(product.id)
                                default_variant = next((v for v in product.variants if v.is_default), None)
                                if default_variant:
                                    price = default_variant.sale_price if default_variant.sale_price else default_variant.price
                                    message += f"📱 **{product.name}**\n"
                                    message += f"   💰 Giá: {float(price):,.0f}đ\n"
                                    message += f"   ⭐ {float(product.avg_rating):.1f}/5\n\n"

                        message += "Bạn muốn xem chi tiết sản phẩm nào? Hoặc cho tôi biết thêm yêu cầu cụ thể hơn nhé (vd: iPhone 15, laptop gaming,...)"
                        dispatcher.utter_message(text=message)
                        session.close()
                        return []

                # Không có keyword -> hỏi clarifying questions
                message = "🤔 Bạn đang tìm sản phẩm gì nhỉ?\n\n"
                message += "Bạn có thể cho tôi biết thêm nhé:\n"
                message += "• 📱 Loại sản phẩm: điện thoại, laptop, tai nghe, đồng hồ...\n"
                message += "• 🏷️ Hãng: Apple, Samsung, Dell, HP, Lenovo...\n"
                message += "• 💰 Mức giá: dưới 10 triệu, 10-20 triệu, trên 20 triệu...\n\n"
                message += "Hoặc bạn có thể xem danh mục sản phẩm của chúng tôi:"

                # Gợi ý danh mục
                categories = session.query(ProductCategory).limit(6).all()
                if categories:
                    message += "\n\n"
                    for cat in categories:
                        message += f"• {cat.name}\n"

                dispatcher.utter_message(text=message)
                session.close()
                return []

            # Build query với ORM
            query = session.query(Product).join(ProductVariant).join(ProductCategory).filter(
                Product.is_active == True,
                ProductVariant.is_default == True
            )

            if product_name:
                query = query.filter(
                    or_(
                        Product.name.like(f"%{product_name}%"),
                        Product.slug.like(f"%{product_name}%")
                    )
                )

            if product_type:
                query = query.filter(ProductCategory.name.like(f"%{product_type}%"))

            if brand:
                query = query.filter(Product.brand.like(f"%{brand}%"))

            products = query.limit(5).all()

            if products:
                message = "🔍 **Tìm thấy các sản phẩm sau:**\n\n"
                for product in products:
                    default_variant = next((v for v in product.variants if v.is_default), None)
                    if default_variant:
                        price = default_variant.sale_price if default_variant.sale_price else default_variant.price
                        stock_status = "✅ Còn hàng" if default_variant.stock_quantity > 0 else "❌ Hết hàng"

                        message += f"📱 **{product.name}**\n"
                        message += f"   💰 Giá: {float(price):,.0f}đ\n"
                        if default_variant.sale_price:
                            message += f"   🏷️ Giá gốc: {float(default_variant.price):,.0f}đ\n"
                        message += f"   {stock_status}\n"
                        if product.short_description:
                            message += f"   📝 {product.short_description}\n"
                        message += f"   ⭐ {float(product.avg_rating):.1f}/5 ({product.review_count} đánh giá)\n\n"

                message += "Bạn muốn xem chi tiết sản phẩm nào?"
            else:
                message = "😔 Xin lỗi, không tìm thấy sản phẩm phù hợp.\n\n"
                message += "Bạn có thể thử:\n"
                message += "• Tìm kiếm với từ khóa khác\n"
                message += "• Cho biết thêm thông tin về hãng, loại sản phẩm\n"
                message += "• Liên hệ hotline để được tư vấn trực tiếp"

            dispatcher.utter_message(text=message)

        except Exception as e:
            print(f"Error in ActionSearchProducts: {e}")
            dispatcher.utter_message(text="Xin lỗi, đã có lỗi xảy ra khi tìm kiếm sản phẩm.")
        finally:
            session.close()

        return []


class ActionGetProductPrice(Action):
    """Lấy giá sản phẩm với ORM"""

    def name(self) -> Text:
        return "action_get_product_price"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        session = db_session.get_session()

        try:
            product_name = tracker.get_slot("product_name")
            product_type = tracker.get_slot("product_type")
            brand = tracker.get_slot("brand")

            # Nếu thiếu thông tin sản phẩm -> hỏi clarifying questions
            if not product_name and not product_type and not brand:
                latest_message = tracker.latest_message.get('text', '')

                # Kiểm tra keyword trong câu hỏi
                keywords = []
                if any(word in latest_message.lower() for word in ['laptop', 'máy tính', 'notebook', 'macbook']):
                    keywords.append('laptop')
                if any(word in latest_message.lower() for word in ['điện thoại', 'dt', 'smartphone', 'iphone', 'samsung']):
                    keywords.append('điện thoại')
                if any(word in latest_message.lower() for word in ['tai nghe', 'headphone', 'airpod']):
                    keywords.append('tai nghe')

                if keywords:
                    # Gợi ý sản phẩm theo keyword
                    category_map = {
                        'laptop': 'Laptop',
                        'điện thoại': 'Điện thoại',
                        'tai nghe': 'Tai nghe'
                    }

                    products = session.query(Product).join(ProductVariant).join(ProductCategory).filter(
                        Product.is_active == True,
                        ProductCategory.name.like(f"%{category_map.get(keywords[0], keywords[0])}%"),
                        ProductVariant.is_default == True
                    ).limit(5).all()

                    if products:
                        message = f"💰 Tôi sẽ giúp bạn xem giá **{keywords[0]}**. Dưới đây là các gợi ý:\n\n"
                        for p in products:
                            v = next((x for x in p.variants if x.is_default), None)
                            if v:
                                price = v.sale_price if v.sale_price else v.price
                                message += f"📱 **{p.name}**\n"
                                message += f"   💵 Giá: {float(price):,.0f}đ\n\n"

                        message += "Bạn muốn xem chi tiết sản phẩm nào?"
                        dispatcher.utter_message(text=message)
                        session.close()
                        return []

                # Không có keyword -> hỏi thông tin
                message = "🤔 Bạn muốn xem giá sản phẩm nào nhỉ?\n\n"
                message += "Bạn có thể cho tôi biết:\n"
                message += "• 📱 Tên sản phẩm: iPhone 15, Macbook Pro, Samsung S24...\n"
                message += "• 🏷️ Hãng: Apple, Samsung, Dell, HP...\n"
                message += "• 📂 Loại: điện thoại, laptop, tai nghe...\n\n"
                message += "Ví dụ: \"iPhone 15 giá bao nhiêu?\" hoặc \"Cho xem giá laptop Dell\""

                dispatcher.utter_message(text=message)
                session.close()
                return []
            
            product = session.query(Product).filter(
                Product.is_active == True,
                Product.name.like(f"%{product_name}%")
            ).first()
            
            if product:
                default_variant = next((v for v in product.variants if v.is_default), None)
                
                if default_variant:
                    price = default_variant.sale_price if default_variant.sale_price else default_variant.price
                    message = f"💰 **{product.name}**\n\n"
                    
                    if default_variant.sale_price:
                        discount_percent = ((float(default_variant.price) - float(default_variant.sale_price)) / float(default_variant.price)) * 100
                        message += f"🏷️ Giá gốc: {float(default_variant.price):,.0f}đ\n"
                        message += f"💵 Giá khuyến mãi: {float(default_variant.sale_price):,.0f}đ\n"
                        message += f"🎉 Tiết kiệm: {discount_percent:.0f}% ({float(default_variant.price - default_variant.sale_price):,.0f}đ)\n"
                    else:
                        message += f"Giá: {float(price):,.0f}đ\n"
                    
                    if default_variant.stock_quantity > 0:
                        message += "\n✅ Sản phẩm đang có sẵn!"
                        if default_variant.stock_quantity <= default_variant.alert_quantity:
                            message += f" (Chỉ còn {default_variant.stock_quantity} sản phẩm)"
                    else:
                        message += "\n❌ Sản phẩm tạm hết hàng"
                    
                    # Thêm thông tin đánh giá
                    if product.review_count > 0:
                        message += f"\n⭐ Đánh giá: {float(product.avg_rating):.1f}/5 ({product.review_count} reviews)"
                else:
                    message = f"Không tìm thấy thông tin giá cho {product.name}"
            else:
                message = f"😔 Không tìm thấy sản phẩm '{product_name}'. Bạn có thể tìm kiếm với từ khóa khác."
            
            dispatcher.utter_message(text=message)
            
        except Exception as e:
            print(f"Error in ActionGetProductPrice: {e}")
            dispatcher.utter_message(text="Xin lỗi, đã có lỗi xảy ra khi lấy giá sản phẩm.")
        finally:
            session.close()
        
        return []


class ActionCheckAvailability(Action):
    """Kiểm tra tồn kho với ORM"""

    def name(self) -> Text:
        return "action_check_availability"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        session = db_session.get_session()

        try:
            product_name = tracker.get_slot("product_name")
            product_type = tracker.get_slot("product_type")
            brand = tracker.get_slot("brand")

            # Nếu thiếu thông tin -> hỏi clarifying questions
            if not product_name and not product_type and not brand:
                latest_message = tracker.latest_message.get('text', '')

                keywords = []
                if any(word in latest_message.lower() for word in ['laptop', 'máy tính', 'macbook']):
                    keywords.append('laptop')
                if any(word in latest_message.lower() for word in ['điện thoại', 'iphone', 'samsung']):
                    keywords.append('điện thoại')
                if any(word in latest_message.lower() for word in ['tai nghe', 'airpod']):
                    keywords.append('tai nghe')

                if keywords:
                    category_map = {
                        'laptop': 'Laptop',
                        'điện thoại': 'Điện thoại',
                        'tai nghe': 'Tai nghe'
                    }

                    products = session.query(Product).join(ProductVariant).join(ProductCategory).filter(
                        Product.is_active == True,
                        ProductCategory.name.like(f"%{category_map.get(keywords[0], keywords[0])}%"),
                        ProductVariant.is_default == True
                    ).limit(5).all()

                    if products:
                        message = f"📦 Tôi sẽ kiểm tra tồn kho cho **{keywords[0]}**. Dưới đây là các gợi ý:\n\n"
                        for p in products:
                            v = next((x for x in p.variants if x.is_default), None)
                            if v:
                                status = "✅ Còn hàng" if v.stock_quantity > 0 else "❌ Hết hàng"
                                message += f"📱 **{p.name}**\n"
                                message += f"   {status}\n\n"

                        message += "Bạn muốn kiểm tra sản phẩm nào?"
                        dispatcher.utter_message(text=message)
                        session.close()
                        return []

                message = "🤔 Bạn muốn kiểm tra tồn kho sản phẩm nào nhỉ?\n\n"
                message += "Bạn có thể cho tôi biết:\n"
                message += "• 📱 Tên sản phẩm: iPhone 15, Macbook Pro...\n"
                message += "• 🏷️ Hãng: Apple, Samsung, Dell...\n"
                message += "• 📂 Loại: điện thoại, laptop, tai nghe...\n\n"
                message += "Ví dụ: \"iPhone 15 còn hàng không?\" hoặc \"Cho xem laptop Dell còn không\""

                dispatcher.utter_message(text=message)
                session.close()
                return []
            
            product = session.query(Product).filter(
                Product.is_active == True,
                Product.name.like(f"%{product_name}%")
            ).first()
            
            if product:
                variants = session.query(ProductVariant).filter(
                    ProductVariant.product_id == product.id,
                    ProductVariant.is_active == True
                ).order_by(ProductVariant.is_default.desc()).limit(5).all()
                
                if variants:
                    message = f"📦 **Tình trạng kho: {product.name}**\n\n"
                    
                    for variant in variants:
                        if variant.stock_quantity > 10:
                            status = "✅ Còn hàng"
                        elif variant.stock_quantity > 0:
                            status = f"⚠️ Còn {variant.stock_quantity} sản phẩm"
                        else:
                            status = "❌ Hết hàng"
                        
                        price = variant.sale_price if variant.sale_price else variant.price
                        message += f"📌 SKU: {variant.sku}\n"
                        message += f"   💰 Giá: {float(price):,.0f}đ\n"
                        message += f"   {status}\n\n"
                    
                    message += "Bạn muốn đặt hàng sản phẩm nào?"
                else:
                    message = f"Không tìm thấy thông tin tồn kho cho '{product.name}'."
            else:
                message = f"Không tìm thấy thông tin tồn kho cho '{product_name}'."
            
            dispatcher.utter_message(text=message)
            
        except Exception as e:
            print(f"Error in ActionCheckAvailability: {e}")
            dispatcher.utter_message(text="Xin lỗi, đã có lỗi xảy ra khi kiểm tra tồn kho.")
        finally:
            session.close()
        
        return []


class ActionGetProductSpecs(Action):
    """Lấy thông số kỹ thuật với ORM"""
    
    def name(self) -> Text:
        return "action_get_product_specs"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        session = db_session.get_session()
        
        try:
            product_name = tracker.get_slot("product_name")
            
            if not product_name:
                dispatcher.utter_message(text="Bạn muốn xem thông số kỹ thuật của sản phẩm nào?")
                return []
            
            product = session.query(Product).filter(
                Product.is_active == True,
                Product.name.like(f"%{product_name}%")
            ).first()
            
            if product:
                message = f"📋 **Thông số kỹ thuật: {product.name}**\n\n"
                message += f"🏢 Thương hiệu: {product.brand}\n"
                message += f"🌍 Xuất xứ: {product.origin}\n"
                message += f"📂 Danh mục: {product.category.name}\n\n"
                
                if product.description:
                    desc = product.description[:500]
                    message += f"📝 Mô tả:\n{desc}...\n\n"
                
                # Lấy FAQs
                faqs = session.query(ProductFAQ).filter(
                    ProductFAQ.product_id == product.id
                ).order_by(ProductFAQ.order).limit(3).all()
                
                if faqs:
                    message += "❓ **Câu hỏi thường gặp:**\n\n"
                    for faq in faqs:
                        message += f"Q: {faq.question}\n"
                        message += f"A: {faq.answer}\n\n"
                
                message += "Bạn cần thông tin chi tiết hơn về sản phẩm này không?"
            else:
                message = f"Không tìm thấy thông tin cho '{product_name}'."
            
            dispatcher.utter_message(text=message)
            
        except Exception as e:
            print(f"Error in ActionGetProductSpecs: {e}")
            dispatcher.utter_message(text="Xin lỗi, đã có lỗi xảy ra khi lấy thông số kỹ thuật.")
        finally:
            session.close()
        
        return []


class ActionCompareProducts(Action):
    """So sánh sản phẩm"""
    
    def name(self) -> Text:
        return "action_compare_products"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "📊 **So sánh sản phẩm**\n\n"
        message += "Để so sánh sản phẩm, vui lòng cho tôi biết tên 2 sản phẩm bạn muốn so sánh.\n\n"
        message += "Ví dụ: 'So sánh iPhone 15 và Samsung S24'"
        
        dispatcher.utter_message(text=message)
        return []


class ActionRecommendProducts(Action):
    """Gợi ý sản phẩm với ORM"""

    def name(self) -> Text:
        return "action_recommend_products"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        session = db_session.get_session()

        try:
            product_type = tracker.get_slot("product_type")
            brand = tracker.get_slot("brand")

            # Nếu không có thông tin -> hỏi clarifying questions
            if not product_type and not brand:
                latest_message = tracker.latest_message.get('text', '')

                # Kiểm tra keyword
                keywords = []
                if any(word in latest_message.lower() for word in ['laptop', 'máy tính', 'notebook', 'macbook']):
                    keywords.append('laptop')
                if any(word in latest_message.lower() for word in ['điện thoại', 'dt', 'smartphone', 'iphone', 'samsung']):
                    keywords.append('điện thoại')
                if any(word in latest_message.lower() for word in ['tai nghe', 'headphone', 'airpod']):
                    keywords.append('tai nghe')
                if any(word in latest_message.lower() for word in ['đồng hồ', 'watch', 'smartwatch']):
                    keywords.append('đồng hồ')

                if keywords:
                    category_map = {
                        'laptop': 'Laptop',
                        'điện thoại': 'Điện thoại',
                        'tai nghe': 'Tai nghe',
                        'đồng hồ': 'Đồng hồ'
                    }

                    query = session.query(Product).join(ProductVariant).join(ProductCategory).filter(
                        Product.is_active == True,
                        ProductVariant.is_default == True,
                        ProductCategory.name.like(f"%{category_map.get(keywords[0], keywords[0])}%")
                    ).order_by(
                        Product.avg_rating.desc(),
                        Product.review_count.desc()
                    ).limit(5).all()

                    if query:
                        message = f"⭐ **Sản phẩm {keywords[0]} được đánh giá cao:**\n\n"
                        for product in query:
                            v = next((x for x in product.variants if x.is_default), None)
                            if v:
                                price = v.sale_price if v.sale_price else v.price
                                message += f"🏆 **{product.name}**\n"
                                message += f"   💰 {float(price):,.0f}đ\n"
                                message += f"   ⭐ {float(product.avg_rating):.1f}/5 ({product.review_count} đánh giá)\n\n"

                        message += "Bạn quan tâm sản phẩm nào?"
                        dispatcher.utter_message(text=message)
                        session.close()
                        return []

            query = session.query(Product).join(ProductVariant).filter(
                Product.is_active == True,
                Product.is_featured == True,
                ProductVariant.is_default == True
            )

            if product_type:
                query = query.join(ProductCategory).filter(
                    ProductCategory.name.like(f"%{product_type}%")
                )

            if brand:
                query = query.filter(Product.brand.like(f"%{brand}%"))

            products = query.order_by(
                Product.avg_rating.desc(),
                Product.review_count.desc()
            ).limit(5).all()

            if products:
                message = "⭐ **Sản phẩm được đề xuất cho bạn:**\n\n"

                for product in products:
                    default_variant = next((v for v in product.variants if v.is_default), None)
                    if default_variant:
                        price = default_variant.sale_price if default_variant.sale_price else default_variant.price
                        rating = f"⭐ {float(product.avg_rating):.1f}" if product.avg_rating > 0 else "Chưa có đánh giá"

                        message += f"🏆 **{product.name}**\n"
                        message += f"   💰 {float(price):,.0f}đ\n"
                        message += f"   {rating} ({product.review_count} đánh giá)\n"
                        if product.short_description:
                            message += f"   📝 {product.short_description}\n"
                        message += "\n"

                message += "Bạn quan tâm đến sản phẩm nào?"
            else:
                message = "🤔 Hiện tại chưa có gợi ý phù hợp.\n\n"
                message += "Bạn có thể cho tôi biết thêm nhé:\n"
                message += "• 📱 Loại sản phẩm: điện thoại, laptop, tai nghe...\n"
                message += "• 🏷️ Hãng yêu thích: Apple, Samsung, Dell...\n"
                message += "• 💰 Mức giá mong muốn\n\n"

                # Hiển thị danh mục
                categories = session.query(ProductCategory).limit(6).all()
                if categories:
                    message += "📂 **Danh mục sản phẩm:**\n"
                    for cat in categories:
                        message += f"• {cat.name}\n"

            dispatcher.utter_message(text=message)
            
        except Exception as e:
            print(f"Error in ActionRecommendProducts: {e}")
            dispatcher.utter_message(text="Xin lỗi, đã có lỗi xảy ra khi gợi ý sản phẩm.")
        finally:
            session.close()
        
        return []
