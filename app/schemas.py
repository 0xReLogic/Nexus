from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, List

class URLCreate(BaseModel):
    original_url: HttpUrl
    custom_code: Optional[str] = None

class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    short_url: str
    created_at: datetime
    click_count: int
    is_active: bool

    class Config:
        from_attributes = True

class ClickResponse(BaseModel):
    id: int
    short_code: str
    clicked_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    referer: Optional[str]
    country: Optional[str]
    city: Optional[str]

    class Config:
        from_attributes = True

class AnalyticsResponse(BaseModel):
    total_clicks: int
    unique_ips: int
    top_countries: List[dict]
    top_referrers: List[dict]
    click_history: List[dict]
    browser_stats: List[dict]
