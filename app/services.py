import string
import random
import validators
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from collections import Counter
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import user_agents

from app.database import URL, Click

class URLService:
    @staticmethod
    def generate_short_code(length: int = 6) -> str:
        """Generate random short code"""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
    
    @staticmethod
    def create_short_url(db: Session, original_url: str, custom_code: Optional[str] = None, creator_ip: Optional[str] = None) -> URL:
        """Create a new short URL"""
        if not validators.url(original_url):
            raise ValueError("Invalid URL format")
        
        # Generate or use custom short code
        if custom_code:
            if db.query(URL).filter(URL.short_code == custom_code).first():
                raise ValueError("Custom code already exists")
            short_code = custom_code
        else:
            # Generate unique short code
            while True:
                short_code = URLService.generate_short_code()
                if not db.query(URL).filter(URL.short_code == short_code).first():
                    break
        
        url_obj = URL(
            original_url=original_url,
            short_code=short_code,
            creator_ip=creator_ip
        )
        db.add(url_obj)
        db.commit()
        db.refresh(url_obj)
        return url_obj
    
    @staticmethod
    def get_url_by_code(db: Session, short_code: str) -> Optional[URL]:
        """Get URL by short code"""
        return db.query(URL).filter(URL.short_code == short_code, URL.is_active == True).first()
    
    @staticmethod
    def increment_click_count(db: Session, short_code: str):
        """Increment click count for URL"""
        url = db.query(URL).filter(URL.short_code == short_code).first()
        if url:
            url.click_count += 1
            db.commit()

class AnalyticsService:
    @staticmethod
    def track_click(db: Session, short_code: str, ip_address: str, user_agent: str, referer: Optional[str] = None):
        """Track a click event"""
        # Parse user agent for browser info
        ua = user_agents.parse(user_agent)
        
        click = Click(
            short_code=short_code,
            ip_address=ip_address,
            user_agent=f"{ua.browser.family} {ua.browser.version_string}",
            referer=referer,
            country="Unknown",  # Would need GeoIP database for real location
            city="Unknown"
        )
        db.add(click)
        db.commit()
        
        # Also increment URL click count
        URLService.increment_click_count(db, short_code)
    
    @staticmethod
    def get_analytics(db: Session, short_code: str) -> Dict:
        """Get analytics for a short URL"""
        clicks = db.query(Click).filter(Click.short_code == short_code).all()
        
        if not clicks:
            return {
                "total_clicks": 0,
                "unique_ips": 0,
                "top_countries": [],
                "top_referrers": [],
                "click_history": [],
                "browser_stats": []
            }
        
        # Calculate metrics
        total_clicks = len(clicks)
        unique_ips = len(set(click.ip_address for click in clicks if click.ip_address))
        
        # Top countries
        countries = [click.country for click in clicks if click.country]
        country_counts = Counter(countries).most_common(5)
        top_countries = [{"country": k, "count": v} for k, v in country_counts]
        
        # Top referrers
        referrers = [click.referer for click in clicks if click.referer]
        referrer_counts = Counter(referrers).most_common(5)
        top_referrers = [{"referrer": k, "count": v} for k, v in referrer_counts]
        
        # Click history (last 30 days by day)
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        recent_clicks = [c for c in clicks if c.clicked_at >= thirty_days_ago]
        
        click_history = {}
        for click in recent_clicks:
            date_key = click.clicked_at.date().isoformat()
            click_history[date_key] = click_history.get(date_key, 0) + 1
        
        click_history_list = [{"date": k, "clicks": v} for k, v in sorted(click_history.items())]
        
        # Browser stats
        browsers = [click.user_agent for click in clicks if click.user_agent]
        browser_counts = Counter(browsers).most_common(5)
        browser_stats = [{"browser": k, "count": v} for k, v in browser_counts]
        
        return {
            "total_clicks": total_clicks,
            "unique_ips": unique_ips,
            "top_countries": top_countries,
            "top_referrers": top_referrers,
            "click_history": click_history_list,
            "browser_stats": browser_stats
        }
