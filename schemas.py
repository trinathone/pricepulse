from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class PriceHistorySchema(BaseModel):
    price: float
    scraped_at: datetime

    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    url: str
    source: str  # 'amazon' or 'ebay'
    target_price: Optional[float] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    target_price: Optional[float] = None
    active: Optional[bool] = None

class ProductSchema(BaseModel):
    id: int
    name: str
    url: str
    source: str
    target_price: Optional[float]
    active: bool
    created_at: datetime
    prices: List[PriceHistorySchema] = []

    class Config:
        from_attributes = True

class PriceAlertSchema(BaseModel):
    product_id: int
    product_name: str
    current_price: float
    target_price: float
    drop_percentage: float
