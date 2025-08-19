# Nexus URL Shortener

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.23-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen.svg)

Advanced URL shortener service with comprehensive analytics and click tracking capabilities.

## Features

- **URL Shortening**: Convert long URLs into short, manageable links
- **Custom Short Codes**: Option to create custom short codes for branded links
- **Advanced Analytics**: Detailed click tracking with metrics including:
  - Total clicks and unique visitors
  - Geographic data (country/city)
  - Browser and device statistics
  - Referrer tracking
  - Click history over time
- **Rate Limiting**: Built-in protection against abuse
- **RESTful API**: Clean, well-documented API endpoints
- **Redis Support**: Optional Redis integration for improved performance
- **Docker Ready**: Easy deployment with Docker and Docker Compose

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLAlchemy with SQLite (easily configurable for PostgreSQL/MySQL)
- **Caching**: Redis (optional)
- **Testing**: Pytest
- **Deployment**: Docker & Docker Compose

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/0xReLogic/Nexus.git
   cd Nexus
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Using Docker Compose (Recommended)**
   ```bash
   docker-compose up -d
   ```

2. **Using Docker only**
   ```bash
   docker build -t nexus .
   docker run -p 8000:8000 nexus
   ```

## API Endpoints

### Create Short URL
```
POST /shorten
Content-Type: application/json

{
  "original_url": "https://example.com",
  "custom_code": "optional-custom-code"
}
```

### Redirect to Original URL
```
GET /{short_code}
```

### Get URL Information
```
GET /api/urls/{short_code}
```

### Get Analytics
```
GET /api/analytics/{short_code}
```

### List All URLs
```
GET /api/urls?skip=0&limit=100
```

## API Documentation

Once the application is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## Example Usage

### Creating a Short URL
```bash
curl -X POST "http://localhost:8000/shorten" \
     -H "Content-Type: application/json" \
     -d '{"original_url": "https://github.com/username/repo"}'
```

Response:
```json
{
  "id": 1,
  "original_url": "https://github.com/username/repo",
  "short_code": "abc123",
  "short_url": "http://localhost:8000/abc123",
  "created_at": "2024-01-01T12:00:00Z",
  "click_count": 0,
  "is_active": true
}
```

### Getting Analytics
```bash
curl "http://localhost:8000/api/analytics/abc123"
```

Response:
```json
{
  "total_clicks": 42,
  "unique_ips": 28,
  "top_countries": [
    {"country": "United States", "count": 15},
    {"country": "Germany", "count": 8}
  ],
  "top_referrers": [
    {"referrer": "https://twitter.com", "count": 12},
    {"referrer": "https://reddit.com", "count": 8}
  ],
  "click_history": [
    {"date": "2024-01-01", "clicks": 5},
    {"date": "2024-01-02", "clicks": 12}
  ],
  "browser_stats": [
    {"browser": "Chrome 91.0", "count": 25},
    {"browser": "Firefox 89.0", "count": 10}
  ]
}
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./nexus.db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `SECRET_KEY` | Secret key for security | `your-secret-key-here` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `*` |
| `BASE_URL` | Base URL for short links | `http://localhost:8000` |

### Rate Limiting

The API includes built-in rate limiting:
- **Default**: 10 requests per minute per IP
- **Configurable**: Modify in `app/middleware.py`
- **Fallback**: In-memory storage if Redis is unavailable

## Testing

Run the test suite:
```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest tests/ -v
```

## Database Schema

### URLs Table
- `id`: Primary key
- `original_url`: The original long URL
- `short_code`: Generated short code
- `created_at`: Creation timestamp
- `click_count`: Number of clicks
- `is_active`: URL status
- `creator_ip`: IP address of creator

### Clicks Table
- `id`: Primary key
- `short_code`: Reference to URL
- `clicked_at`: Click timestamp
- `ip_address`: Visitor IP
- `user_agent`: Browser information
- `referer`: Referring website
- `country`: Visitor country
- `city`: Visitor city

## Security Features

- **Input validation**: URL format validation
- **Rate limiting**: Prevents abuse
- **IP tracking**: For analytics and security
- **CORS protection**: Configurable origins
- **SQL injection protection**: SQLAlchemy ORM

## Performance Considerations

- **Redis caching**: Optional Redis integration for improved performance
- **Database indexing**: Optimized queries with proper indexes
- **Connection pooling**: Efficient database connections
- **Async support**: FastAPI's async capabilities

## Deployment

### Production Deployment

1. **Set up environment variables**
   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost/nexus"
   export REDIS_URL="redis://localhost:6379"
   export SECRET_KEY="your-strong-secret-key"
   export BASE_URL="https://yourdomain.com"
   ```

2. **Use production database**
   - PostgreSQL recommended for production
   - Update `DATABASE_URL` accordingly

3. **Deploy with Docker**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Health Check

The API provides a health check endpoint:
```
GET /
```

Returns service status and version information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For questions, issues, or contributions, please open an issue on GitHub.
