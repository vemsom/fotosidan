# Fotosidan - Personal Photo Gallery

A clean, minimalist photo gallery web application with admin interface for managing photos, tags, and metadata.

## Features

- **Public Gallery**: Masonry grid layout with no navigation or links—just photos
- **Admin Interface**: Upload, organize, and manage photos with Lightroom keyword support
- **EXIF Metadata**: Automatic extraction of camera settings and dates
- **Lightroom Keywords**: Auto-import from XMP metadata in JPEG files
- **Image Optimization**: Automatic resizing to thumbnail (600px) and display (2560px) sizes
- **Tag Management**: Add, edit, and remove tags from photos
- **Drag-to-Reorder**: Reorder photos in the gallery with drag-and-drop
- **Visibility Control**: Toggle photo visibility without deleting

## Setup

### Installation

1. Clone the repository:
```bash
cd /home/fredrik/Projects/fotosidan
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

4. Create `.env` file from example:
```bash
cp .env.example .env
```

5. Run the application:
```bash
uvicorn fotosidan.main:app --reload
```

Visit `http://localhost:8000` for the gallery and `http://localhost:8000/admin` for the admin interface.

### Environment Variables

- `DATABASE_URL`: SQLite database path (default: `sqlite:///storage/fotosidan.db`)
- `STORAGE_PATH`: Where to store uploaded photos (default: `storage`)
- `SITE_TITLE`: Gallery title (default: `Fotosidan`)
- `ADMIN_ENABLED`: Enable/disable admin interface (default: `true`)
- `ADMIN_SECRET`: Optional HTTP Basic auth password for admin (leave empty for local use)
- `HOST`: Server host (default: `127.0.0.1`)
- `PORT`: Server port (default: `8000`)

## Usage

### Public Gallery

- Navigate to `http://localhost:8000`
- Click any photo to view fullsize in a lightbox
- Use arrow keys or buttons to navigate between photos

### Admin Interface

1. Go to `http://localhost:8000/admin/photos`
2. Click **Upload Photo** to add a new photo
3. Select a JPEG file—Lightroom keywords are auto-imported as tags
4. Edit photo details: title, description, EXIF data, and tags
5. Drag photos to reorder them
6. Toggle visibility or delete as needed

## Deployment

To deploy publicly with admin disabled:

```bash
ADMIN_ENABLED=false uvicorn fotosidan.main:app --host 0.0.0.0 --port 8000
```

For optional HTTP Basic authentication when admin is enabled, set `ADMIN_SECRET` in your environment.

## Database Schema

- **photos**: Photo records with EXIF data and metadata
- **tags**: Tag names
- **photo_tags**: Many-to-many relationship between photos and tags

## Technical Stack

- **Backend**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **Image Processing**: Pillow
- **Frontend**: Jinja2 templates, HTMX, Sortable.js
- **CSS**: Vanilla CSS with masonry layout

## File Structure

```
fotosidan/
├── fotosidan/
│   ├── main.py              # App factory
│   ├── config.py            # Settings
│   ├── database.py          # ORM setup
│   ├── models.py            # Database models
│   └── routes/
│       ├── public.py        # Gallery routes
│       └── admin.py         # Admin routes + EXIF/XMP extraction
├── static/
│   ├── gallery.css          # Gallery styling
│   ├── admin.css            # Admin styling
│   └── lightbox.js          # Photo lightbox
├── storage/
│   ├── photos/
│   │   ├── thumb/           # 600px thumbnails
│   │   └── display/         # 2560px display images
│   └── fotosidan.db         # SQLite database
└── pyproject.toml           # Dependencies
```

## License

Created with ♥
