"""
Promotion-related Actions using SQLAlchemy ORM
Actions liên quan đến khuyến mãi
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from datetime import datetime
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.models import Coupon, Product, ProductVariant, ProductReview, db_session


class ActionGetCoupons(Action):
    """Lấy danh sách mã giảm giá với ORM"""
    
    def name(self) -> Text:
        return "action_get_coupons"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        session = db_session.get_session()
        
        try:
            now = datetime.now()
            
            coupons = session.query(Coupon).filter(
                Coupon.is_active == True,
                Coupon.is_public == True,
                Coupon.start_date <= now,
                Coupon.end_date >= now
            ).order_by(Coupon.value.desc()).limit(5).all()
            
            if coupons:
                message = "🎁 **Mã giảm giá hiện có:**\n\n"
                
                for coupon in coupons:
                    message += f"🏷️ **{coupon.code}**\n"
                    message += f"   📝 {coupon.name}\n"
                    
                    if coupon.type == 'percentage':
                        message += f"   💰 Giảm {float(coupon.value):.0f}%\n"
                        if coupon.max_discount:
                            message += f"   📊 Giảm tối đa: {float(coupon.max_discount):,.0f}đ\n"
                    elif coupon.type == 'fixed':
                        message += f"   💰 Giảm {float(coupon.value):,.0f}đ\n"
                    else:
                        message += f"   🚚 Miễn phí vận chuyển\n"
                    
                    if coupon.min_order_value > 0:
                        message += f"   📦 Đơn tối thiểu: {float(coupon.min_order_value):,.0f}đ\n"
                    
                    if coupon.usage_limit:
                        remaining = coupon.usage_limit - coupon.used_count
                        message += f"   🎯 Còn lại: {remaining}/{coupon.usage_limit} lượt\n"
                    
                    message += f"   ⏰ HSD: {coupon.end_date.strftime('%d/%m/%Y')}\n\n"
                
                message += "💡 **Cách sử dụng:**\n"
                message += "Nhập mã khi thanh toán để được giảm giá!\n\n"
                message += "Bạn muốn biết thêm về mã nào?"
            else:
                message = "😔 Hiện tại chưa có mã giảm giá. Vui lòng theo dõi fanpage để cập nhật khuyến mãi mới nhất!"
            
            dispatcher.utter_message(text=message)
            
        except Exception as e:
            print(f"Error in ActionGetCoupons: {e}")
            dispatcher.utter_message(text="Xin lỗi, đã có lỗi xảy ra khi lấy mã giảm giá.")
        finally:
            session.close()
        
        return []


class ActionGetPromotions(Action):
    """Lấy thông tin khuyến mãi với ORM"""
    
    def name(self) -> Text:
        return "action_get_promotions"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        session = db_session.get_session()
        
        try:
            # Lấy sản phẩm đang sale
            products = session.query(Product, ProductVariant).join(
                ProductVariant, Product.id == ProductVariant.product_id
            ).filter(
                Product.is_active == True,
                ProductVariant.is_default == True,
                ProductVariant.sale_price.isnot(None)
            ).order_by(
                ((ProductVariant.price - ProductVariant.sale_price) / ProductVariant.price).desc()
            ).limit(5).all()
            
            message = "🔥 **KHUYẾN MÃI HOT**\n\n"
            
            if products:
                message += "⚡ **Sản phẩm đang giảm giá:**\n\n"
                for product, variant in products:
                    discount = ((float(variant.price) - float(variant.sale_price)) / float(variant.price)) * 100
                    saved = float(variant.price) - float(variant.sale_price)
                    
                    message += f"🎯 **{product.name}**\n"
                    message += f"   💵 {float(variant.sale_price):,.0f}đ\n"
                    message += f"   🏷️ Giá gốc: {float(variant.price):,.0f}đ\n"
                    message += f"   🎉 Giảm {discount:.0f}% (Tiết kiệm {saved:,.0f}đ)\n\n"
            
            # Lấy coupon hot
            now = datetime.now()
            coupons = session.query(Coupon).filter(
                Coupon.is_active == True,
                Coupon.is_public == True,
                Coupon.start_date <= now,
                Coupon.end_date >= now
            ).order_by(Coupon.value.desc()).limit(3).all()
            
            if coupons:
                message += "🎁 **Mã giảm giá nổi bật:**\n\n"
                for coupon in coupons:
                    if coupon.type == 'percentage':
                        message += f"• **{coupon.code}**: Giảm {float(coupon.value):.0f}%\n"
                    elif coupon.type == 'fixed':
                        message += f"• **{coupon.code}**: Giảm {float(coupon.value):,.0f}đ\n"
                    else:
                        message += f"• **{coupon.code}**: Miễn phí ship\n"
            
            message += "\n🎊 **Ưu đãi thêm:**\n"
            message += "• Trả góp 0% qua thẻ tín dụng\n"
            message += "• Tích điểm đổi quà\n"
            message += "• Bảo hành mở rộng\n"
            message += "• Giao hàng miễn phí\n\n"
            message += "⏰ **Nhanh tay đặt hàng để không bỏ lỡ!**"
            
            dispatcher.utter_message(text=message)
            
        except Exception as e:
            print(f"Error in ActionGetPromotions: {e}")
            dispatcher.utter_message(text="Xin lỗi, đã có lỗi xảy ra khi lấy thông tin khuyến mãi.")
        finally:
            session.close()
        
        return []


class ActionGetAccountInfo(Action):
    """Lấy thông tin tài khoản"""
    
    def name(self) -> Text:
        return "action_get_account_info"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "👤 **Thông tin tài khoản**\n\n"
        message += "Để xem thông tin tài khoản, bạn vui lòng:\n\n"
        message += "1️⃣ Đăng nhập vào website\n"
        message += "2️⃣ Vào mục 'Tài khoản của tôi'\n\n"
        message += "Hoặc cung cấp email/số điện thoại để tôi tra cứu.\n\n"
        message += "📋 **Thông tin có thể xem:**\n"
        message += "• Thông tin cá nhân\n"
        message += "• Lịch sử đơn hàng\n"
        message += "• Điểm tích lũy\n"
        message += "• Địa chỉ giao hàng\n"
        message += "• Sản phẩm yêu thích"
        
        dispatcher.utter_message(text=message)
        return []


class ActionGetNewArrivals(Action):
    """Lấy sản phẩm mới về"""

    def name(self) -> Text:
        return "action_get_new_arrivals"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        session = db_session.get_session()

        try:
            products = session.query(Product).filter(
                Product.is_active == True
            ).order_by(Product.created_at.desc()).limit(6).all()

            if products:
                message = "🆕 **Sản phẩm mới nhất:**\n\n"
                for p in products:
                    message += f"• **{p.name}**"
                    if p.brand:
                        message += f" ({p.brand})"
                    message += "\n"
                message += "\nXem chi tiết tại website hoặc hỏi tôi về sản phẩm bạn quan tâm!"
            else:
                message = "Hiện chưa có thông tin sản phẩm mới. Vui lòng theo dõi fanpage để cập nhật!"

            dispatcher.utter_message(text=message)

        except Exception as e:
            print(f"Error in ActionGetNewArrivals: {e}")
            dispatcher.utter_message(text="Xin lỗi, đã có lỗi xảy ra khi lấy danh sách sản phẩm mới.")
        finally:
            session.close()

        return []


class ActionGetFlashSale(Action):
    """Lấy thông tin flash sale"""

    def name(self) -> Text:
        return "action_get_flash_sale"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        session = db_session.get_session()

        try:
            products = session.query(Product, ProductVariant).join(
                ProductVariant, Product.id == ProductVariant.product_id
            ).filter(
                Product.is_active == True,
                ProductVariant.is_default == True,
                ProductVariant.sale_price.isnot(None)
            ).order_by(
                ((ProductVariant.price - ProductVariant.sale_price) / ProductVariant.price).desc()
            ).limit(5).all()

            if products:
                message = "⚡ **FLASH SALE - Giảm giá sốc!**\n\n"
                for product, variant in products:
                    discount = ((float(variant.price) - float(variant.sale_price)) / float(variant.price)) * 100
                    message += f"🔥 **{product.name}**\n"
                    message += f"   💥 Giảm {discount:.0f}%: {float(variant.sale_price):,.0f}đ\n\n"
                message += "⏰ Nhanh tay đặt hàng kẻo hết!"
            else:
                message = "⚡ Hiện chưa có flash sale. Theo dõi fanpage để không bỏ lỡ deal hot!"

            dispatcher.utter_message(text=message)

        except Exception as e:
            print(f"Error in ActionGetFlashSale: {e}")
            dispatcher.utter_message(text="Xin lỗi, đã có lỗi xảy ra khi lấy thông tin flash sale.")
        finally:
            session.close()

        return []


class ActionGetProductReviews(Action):
    """Lấy đánh giá sản phẩm"""

    def name(self) -> Text:
        return "action_get_product_reviews"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        session = db_session.get_session()
        product_name = tracker.get_slot("product_name")

        try:
            query = session.query(ProductReview).join(
                Product, ProductReview.product_id == Product.id
            ).filter(ProductReview.is_approved == True)

            if product_name:
                query = query.filter(Product.name.ilike(f"%{product_name}%"))

            reviews = query.order_by(ProductReview.created_at.desc()).limit(5).all()

            if reviews:
                avg = sum(r.rating for r in reviews) / len(reviews)
                message = f"⭐ **Đánh giá sản phẩm** (TB: {avg:.1f}/5)\n\n"
                for r in reviews:
                    stars = "⭐" * r.rating
                    message += f"{stars} **{r.title or 'Đánh giá'}**\n"
                    if r.comment:
                        message += f"   {r.comment[:100]}{'...' if len(r.comment) > 100 else ''}\n"
                    message += "\n"
            else:
                name_str = f" cho **{product_name}**" if product_name else ""
                message = f"Chưa có đánh giá{name_str}. Hãy là người đầu tiên đánh giá!"

            dispatcher.utter_message(text=message)

        except Exception as e:
            print(f"Error in ActionGetProductReviews: {e}")
            dispatcher.utter_message(text="Xin lỗi, đã có lỗi xảy ra khi lấy đánh giá sản phẩm.")
        finally:
            session.close()

        return []


class ActionGetLoyaltyPoints(Action):
    """Kiểm tra điểm tích lũy"""
    
    def name(self) -> Text:
        return "action_get_loyalty_points"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "⭐ **Chương trình tích điểm**\n\n"
        message += "🎁 **Quy đổi điểm:**\n"
        message += "• Mỗi 100.000đ mua hàng = 10 điểm\n"
        message += "• 100 điểm = 10.000đ giảm giá\n"
        message += "• Điểm có hiệu lực 12 tháng\n\n"
        message += "🏆 **Hạng thành viên:**\n"
        message += "• 🥈 Bạc (0-499 điểm): Giảm 5%\n"
        message += "• 🥇 Vàng (500-999 điểm): Giảm 10%\n"
        message += "• 💎 Kim cương (1000+ điểm): Giảm 15%\n\n"
        message += "🎯 **Cách tích điểm:**\n"
        message += "• Mua hàng\n"
        message += "• Viết đánh giá sản phẩm\n"
        message += "• Giới thiệu bạn bè\n"
        message += "• Tham gia sự kiện\n\n"
        message += "💡 **Cách sử dụng điểm:**\n"
        message += "• Đổi mã giảm giá\n"
        message += "• Đổi quà tặng\n"
        message += "• Giảm giá trực tiếp khi mua hàng\n\n"
        message += "Để kiểm tra điểm của bạn, vui lòng cung cấp email hoặc số điện thoại."
        
        dispatcher.utter_message(text=message)
        return []
