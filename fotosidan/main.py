from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path
from dotenv import load_dotenv
import os

from .config import settings
from .database import init_db
from .routes import public

# Load .env file
load_dotenv()

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(title=settings.site_title)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Register public routes (always)
app.include_router(public.router)

# Only register admin routes if ENABLE_ADMIN env var is set
# This ensures admin routes are NOT exposed on public port 8000
if os.getenv("ENABLE_ADMIN", "false").lower() == "true" and settings.admin_enabled:
    from .routes import admin
    app.include_router(admin.router, prefix="/admin")
