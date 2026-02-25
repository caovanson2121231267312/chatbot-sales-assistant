"""
Main Actions File - Import all actions from modules
File actions chính - Import tất cả actions từ các modules
"""

# Import all actions from separate modules
from actions.product_actions import (
    ActionSearchProducts,
    ActionGetProductPrice,
    ActionCheckAvailability,
    ActionGetProductSpecs,
    ActionCompareProducts,
    ActionRecommendProducts
)

from actions.order_actions import (
    ActionCheckOrderStatus,
    ActionTrackOrder,
    ActionCancelOrder,
    ActionReturnOrder
)

from actions.promotion_actions import (
    ActionGetCoupons,
    ActionGetPromotions,
    ActionGetAccountInfo,
    ActionGetLoyaltyPoints,
    ActionGetNewArrivals,
    ActionGetFlashSale,
    ActionGetProductReviews
)

# Export all actions
__all__ = [
    'ActionSearchProducts',
    'ActionGetProductPrice',
    'ActionCheckAvailability',
    'ActionGetProductSpecs',
    'ActionCompareProducts',
    'ActionRecommendProducts',
    'ActionCheckOrderStatus',
    'ActionTrackOrder',
    'ActionCancelOrder',
    'ActionReturnOrder',
    'ActionGetCoupons',
    'ActionGetPromotions',
    'ActionGetAccountInfo',
    'ActionGetLoyaltyPoints',
    'ActionGetNewArrivals',
    'ActionGetFlashSale',
    'ActionGetProductReviews',
]
