from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from app.database import get_db
from app.schemas import URLCreate, URLResponse, AnalyticsResponse
from app.services import URLService, AnalyticsService

load_dotenv()

app = FastAPI(
    title="Nexus URL Shortener",
    description="Advanced URL shortener with detailed analytics",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Nexus URL Shortener API",
        "version": "1.0.0",
        "status": "active"
    }

@app.post("/shorten", response_model=URLResponse)
async def create_short_url(
    url_data: URLCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new short URL"""
    try:
        creator_ip = request.client.host
        url_obj = URLService.create_short_url(
            db=db,
            original_url=str(url_data.original_url),
            custom_code=url_data.custom_code,
            creator_ip=creator_ip
        )
        
        return URLResponse(
            id=url_obj.id,
            original_url=url_obj.original_url,
            short_code=url_obj.short_code,
            short_url=f"{BASE_URL}/{url_obj.short_code}",
            created_at=url_obj.created_at,
            click_count=url_obj.click_count,
            is_active=url_obj.is_active
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/{short_code}")
async def redirect_url(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Redirect to original URL and track analytics"""
    url_obj = URLService.get_url_by_code(db, short_code)
    
    if not url_obj:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    # Track the click
    try:
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent", "")
        referer = request.headers.get("referer")
        
        AnalyticsService.track_click(
            db=db,
            short_code=short_code,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer
        )
    except Exception:
        # Don't fail redirect if analytics tracking fails
        pass
    
    return RedirectResponse(url=url_obj.original_url, status_code=302)

@app.get("/api/urls/{short_code}", response_model=URLResponse)
async def get_url_info(short_code: str, db: Session = Depends(get_db)):
    """Get URL information without redirecting"""
    url_obj = URLService.get_url_by_code(db, short_code)
    
    if not url_obj:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    return URLResponse(
        id=url_obj.id,
        original_url=url_obj.original_url,
        short_code=url_obj.short_code,
        short_url=f"{BASE_URL}/{url_obj.short_code}",
        created_at=url_obj.created_at,
        click_count=url_obj.click_count,
        is_active=url_obj.is_active
    )

@app.get("/api/analytics/{short_code}", response_model=AnalyticsResponse)
async def get_analytics(short_code: str, db: Session = Depends(get_db)):
    """Get detailed analytics for a short URL"""
    # Verify URL exists
    url_obj = URLService.get_url_by_code(db, short_code)
    if not url_obj:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    analytics_data = AnalyticsService.get_analytics(db, short_code)
    
    return AnalyticsResponse(**analytics_data)

@app.get("/api/urls")
async def list_urls(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all URLs (for admin purposes)"""
    from app.database import URL
    urls = db.query(URL).offset(skip).limit(limit).all()
    
    return [
        URLResponse(
            id=url.id,
            original_url=url.original_url,
            short_code=url.short_code,
            short_url=f"{BASE_URL}/{url.short_code}",
            created_at=url.created_at,
            click_count=url.click_count,
            is_active=url.is_active
        )
        for url in urls
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
