# Docker Deployment Guide

## Architecture

- **Port 8000**: Public gallery (exposed externally)
- **Port 8001**: Admin portal (NOT exposed - local only, requires Bearer token)

## Quick Start with Portainer

### 1. Generate Admin Secret
Generate a strong random secret for admin authentication:
```bash
openssl rand -hex 32
```

### 2. In Portainer - Add Stack

1. Go to **Stacks** → **Add Stack**
2. Paste the content from `docker-compose.yml`
3. Under **Environment Variables**, add:
   - `ADMIN_SECRET`: Your generated secret from step 1
   - `SITE_TITLE`: Gallery title (optional, default: "Fotosidan")

4. Click **Deploy the stack**

### 3. Access the Gallery

- **Public Gallery**: `http://your-server:8000` (publicly accessible)
- **Admin Portal**: Port 8001 is **NOT exposed** to the network
  - Admin is protected by Bearer token authentication
  - Can only be accessed with valid `Authorization: Bearer <ADMIN_SECRET>` header

## Admin Access

### From Server (SSH)

```bash
# SSH into your server, then use curl to access admin on port 8001
ADMIN_SECRET="your_secret_here"

# List photos
curl -H "Authorization: Bearer $ADMIN_SECRET" \
  http://localhost:8001/admin/photos

# Upload a photo
curl -H "Authorization: Bearer $ADMIN_SECRET" \
  -F "file=@photo.jpg" \
  http://localhost:8001/admin/photos/upload

# Get photo details
curl -H "Authorization: Bearer $ADMIN_SECRET" \
  http://localhost:8001/admin/photos/1
```

### From Remote (Not Directly)

The admin portal on port 8001 is **not exposed externally**. To manage photos remotely, you can:

1. **SSH Tunnel** (forward port 8001 locally):
   ```bash
   ssh -L 8001:localhost:8001 user@your-server
   # Then access http://localhost:8001/admin with Bearer token
   ```

2. **Build a web UI** that communicates with the API using the Bearer token

3. **Use the public gallery UI** with Bearer token in JavaScript headers

### Security Features

✅ **Admin authentication** - Requires valid `ADMIN_SECRET` token in `Authorization` header
✅ **Separate port** - Admin portal runs on different port (8001, not exposed)
✅ **HTML escaping** - Prevents XSS vulnerabilities
✅ **File upload limits** - Max 50MB per image (configurable)
✅ **Security headers** - HSTS, X-Frame-Options, X-Content-Type-Options
✅ **Local-only access** - Admin port bound to 127.0.0.1 inside container

## Environment Variables

```
ADMIN_SECRET          # REQUIRED: Bearer token for admin access
SITE_TITLE           # Gallery title (default: "Fotosidan")
DATABASE_URL         # SQLite URL (default: sqlite:///storage/fotosidan.db)
STORAGE_PATH         # Storage directory (default: /app/storage)
ADMIN_ENABLED        # Enable admin panel (default: true)
MAX_UPLOAD_SIZE      # Max upload size in bytes (default: 52428800 = 50MB)
ADMIN_PORT           # Admin port (default: 8001)
```

## Persistent Storage

Photos are stored in Docker volume `fotosidan-storage`. They persist across container restarts.

To backup:
```bash
docker run --rm -v fotosidan-storage:/storage -v $(pwd):/backup \
  alpine tar czf /backup/fotosidan-backup.tar.gz -C /storage .
```

## Logs

View logs in Portainer or via CLI:
```bash
docker logs fotosidan
```

## Behind a Reverse Proxy

If using nginx, add your proxy configuration for the **public gallery only**:

```nginx
server {
    listen 80;
    server_name gallery.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then use Let's Encrypt for HTTPS.

**Note**: Do NOT expose port 8001 through the reverse proxy.
