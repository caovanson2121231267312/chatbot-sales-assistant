"""
Order-related Actions using SQLAlchemy ORM
Actions liên quan đến đơn hàng
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from sqlalchemy import or_
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from database.models import Order, OrderItem, User, db_session


class ActionCheckOrderStatus(Action):
    """Kiểm tra trạng thái đơn hàng với ORM"""
    
    def name(self) -> Text:
        return "action_check_order_status"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        session = db_session.get_session()
        
        try:
            order_number = tracker.get_slot("order_number")
            
            if not order_number:
                message = "Vui lòng cung cấp mã đơn hàng hoặc số điện thoại đặt hàng để tôi kiểm tra.\n\n"
                message += "Ví dụ: 'Kiểm tra đơn hàng DH123456'"
                dispatcher.utter_message(text=message)
                return []
            
            order = session.query(Order).filter(
                Order.order_number == order_number
            ).first()
            
            if order:
                status_map = {
                    'pending': '⏳ Chờ xác nhận',
                    'confirmed': '✅ Đã xác nhận',
                    'processing': '📦 Đang xử lý',
                    'ready_to_ship': '🚚 Sẵn sàng giao',
                    'shipping': '🚚 Đang giao hàng',
                    'delivered': '✅ Đã giao hàng',
                    'completed': '🎉 Hoàn thành',
                    'cancelled': '❌ Đã hủy',
                    'refunding': '💰 Đang hoàn tiền',
                    'refunded': '💰 Đã hoàn tiền',
                    'returned': '🔄 Đã trả hàng'
                }
                
                payment_status_map = {
                    'pending': '⏳ Chờ thanh toán',
                    'paid': '✅ Đã thanh toán',
                    'failed': '❌ Thanh toán thất bại',
                    'refunded': '💰 Đã hoàn tiền',
                    'partially_refunded': '💰 Hoàn một phần'
                }
                
                message = f"📋 **Thông tin đơn hàng: {order.order_number}**\n\n"
                message += f"👤 Khách hàng: {order.customer_name}\n"
                message += f"📅 Ngày đặt: {order.created_at.strftime('%d/%m/%Y %H:%M')}\n"
                message += f"💰 Tổng tiền: {float(order.total):,.0f}đ\n"
                message += f"📦 Trạng thái: {status_map.get(order.status, order.status)}\n"
                message += f"💳 Thanh toán: {payment_status_map.get(order.payment_status, order.payment_status)}\n"
                
                if order.tracking_number:
                    message += f"🚚 Mã vận đơn: {order.tracking_number}\n"
                
                if order.estimated_delivery_date:
                    message += f"📅 Dự kiến giao: {order.estimated_delivery_date.strftime('%d/%m/%Y')}\n"
                
                # Hiển thị sản phẩm trong đơn
                items = session.query(OrderItem).filter(
                    OrderItem.order_id == order.id
                ).limit(3).all()
                
                if items:
                    message += "\n📦 **Sản phẩm:**\n"
                    for item in items:
                        message += f"   • {item.product_name} x{item.quantity}\n"
                
                message += "\nBạn cần hỗ trợ gì thêm về đơn hàng này?"
            else:
                message = f"❌ Không tìm thấy đơn hàng '{order_number}'. Vui lòng kiểm tra lại mã đơn hàng."
            
            dispatcher.utter_message(text=message)
            
        except Exception as e:
            print(f"Error in ActionCheckOrderStatus: {e}")
            dispatcher.utter_message(text="Xin lỗi, đã có lỗi xảy ra khi kiểm tra đơn hàng.")
        finally:
            session.close()
        
        return []


class ActionTrackOrder(Action):
    """Theo dõi vận chuyển"""
    
    def name(self) -> Text:
        return "action_track_order"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "🚚 **Theo dõi vận chuyển**\n\n"
        message += "Để theo dõi vận chuyển, vui lòng cung cấp:\n\n"
        message += "• Mã đơn hàng (VD: DH123456)\n"
        message += "• Hoặc mã vận đơn\n\n"
        message += "Tôi sẽ kiểm tra tình trạng giao hàng cho bạn!"
        
        dispatcher.utter_message(text=message)
        return []


class ActionCancelOrder(Action):
    """Hủy đơn hàng"""
    
    def name(self) -> Text:
        return "action_cancel_order"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "❌ **Hủy đơn hàng**\n\n"
        message += "Để hủy đơn hàng, bạn cần:\n\n"
        message += "1️⃣ Cung cấp mã đơn hàng\n"
        message += "2️⃣ Lý do hủy đơn\n\n"
        message += "⚠️ **Lưu ý:**\n"
        message += "• Chỉ hủy được đơn hàng chưa giao\n"
        message += "• Đơn đã thanh toán sẽ được hoàn tiền trong 3-5 ngày\n"
        message += "• Đơn đang giao không thể hủy\n\n"
        message += "Vui lòng liên hệ hotline hoặc cung cấp mã đơn hàng để tôi hỗ trợ."
        
        dispatcher.utter_message(text=message)
        return []


class ActionReturnOrder(Action):
    """Trả hàng hoàn tiền"""
    
    def name(self) -> Text:
        return "action_return_order"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        message = "🔄 **Chính sách đổi trả**\n\n"
        message += "✅ **Điều kiện đổi trả:**\n"
        message += "• Trong vòng 7 ngày kể từ khi nhận hàng\n"
        message += "• Sản phẩm còn nguyên seal, đầy đủ phụ kiện\n"
        message += "• Có hóa đơn mua hàng\n"
        message += "• Sản phẩm chưa qua sử dụng\n\n"
        message += "📝 **Quy trình đổi trả:**\n"
        message += "1. Liên hệ hotline với mã đơn hàng\n"
        message += "2. Gửi ảnh sản phẩm cần đổi/trả\n"
        message += "3. Chúng tôi sẽ thu hồi và xử lý trong 24h\n"
        message += "4. Đổi sản phẩm mới hoặc hoàn tiền\n\n"
        message += "💰 **Hoàn tiền:**\n"
        message += "• Hoàn tiền trong 3-5 ngày làm việc\n"
        message += "• Hoàn về tài khoản/ví đã thanh toán\n\n"
        message += "🎁 **Trường hợp đặc biệt:**\n"
        message += "• Sản phẩm lỗi: Đổi mới trong 30 ngày\n"
        message += "• Giao sai hàng: Đổi ngay không mất phí\n\n"
        message += "Bạn cần hỗ trợ đổi trả đơn hàng nào?"
        
        dispatcher.utter_message(text=message)
        return []
