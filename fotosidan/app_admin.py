"""Admin app (with admin routes)"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path
from dotenv import load_dotenv

from .config import settings
from .database import init_db
from .routes import admin

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

# Custom 404 handler
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Not Found</title>
            <style>
                body { font-family: system-ui, sans-serif; padding: 40px; background: white; }
                h1 { color: #333; }
                p { color: #666; }
                a { color: #0066cc; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>Page Not Found</h1>
            <p>The requested page does not exist.</p>
            <a href="/">← Back to admin</a>
        </body>
        </html>
        """,
        status_code=404,
    )

# Register admin routes at root (no /admin prefix)
if settings.admin_enabled:
    app.include_router(admin.router)
