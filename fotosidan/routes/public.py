import html
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Photo
from ..config import settings
from pathlib import Path

router = APIRouter()


@router.get("/")
async def gallery(db: Session = Depends(get_db)):
    """Serve the public gallery page with all visible photos."""
    from fastapi.responses import HTMLResponse

    # Get all visible photos ordered by sort_order
    photos = db.query(Photo).filter(Photo.visible == True).order_by(Photo.sort_order).all()

    # Collect all unique tags from all photos
    all_tags = set()
    for photo in photos:
        for tag in photo.tags:
            all_tags.add(tag.name)
    all_tags = sorted(all_tags)

    # Build gallery HTML (both grid-2 and grid-1 versions)
    gallery_html = ""
    for photo in photos:
        tags_str = " ".join([f'<span class="photo-tag">{html.escape(tag.name)}</span>' for tag in photo.tags])
        tags_attr = ",".join([tag.name.lower() for tag in photo.tags])
        safe_title = html.escape(photo.title or 'Photo')
        gallery_html += f"""        <figure class="photo-item" data-photo-id="{photo.id}" data-tags="{tags_attr}">
            <img class="grid-2-img" src="/photos/{photo.uuid}/thumb" alt="{safe_title}" loading="lazy">
            <img class="grid-1-img" srcset="/photos/{photo.uuid}/medium 1400w, /photos/{photo.uuid}/display 2400w" src="/photos/{photo.uuid}/medium" alt="{safe_title}" loading="lazy" style="display: none;">
            <div class="photo-tags">{tags_str}</div>
        </figure>
"""

    # Build slideshow HTML
    slideshow_html = ""
    for idx, photo in enumerate(photos):
        tags_str = " ".join([f'<span class="photo-tag">{tag.name}</span>' for tag in photo.tags])
        tags_attr = ",".join([tag.name.lower() for tag in photo.tags])
        slideshow_html += f"""        <div class="slideshow-item" data-index="{idx}" data-tags="{tags_attr}" style="display: {'block' if idx == 0 else 'none'};">
            <img src="/photos/{photo.uuid}/display" alt="{photo.title or 'Photo'}" class="slideshow-image">
            <div class="photo-tags">{tags_str}</div>
            <div class="slideshow-controls">
                <button onclick="prevSlide()" title="Previous">Previous</button>
                <button onclick="nextSlide()" title="Next">Next</button>
            </div>
        </div>
"""

    # Build tags dropdown HTML
    tags_dropdown_html = ""
    if all_tags:
        tags_dropdown_html = '<div class="tags-dropdown">\n'
        for tag in all_tags:
            tags_dropdown_html += f'            <span class="dropdown-tag" data-tag-name="{tag.lower()}">{tag}</span>\n'
        tags_dropdown_html += '        </div>'

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{settings.site_title}</title>
    <link rel="stylesheet" href="/static/gallery.css">
</head>
<body>
    <div class="controls">
        <button id="grid-2-btn" class="active" onclick="showGrid2()">Grid</button>
        <button id="grid-1-btn" onclick="showGrid1()">List</button>
        <button id="slideshow-btn" onclick="showSlideshow()">Slideshow</button>
        <button id="tags-btn" onclick="toggleTagsDropdown()">Tags</button>
        {tags_dropdown_html}
    </div>

    <div id="gallery-container" class="gallery active grid-2">
{gallery_html}
    </div>

    <div id="slideshow-container" class="slideshow">
{slideshow_html}
    </div>

    <script src="/static/lightbox.js"></script>
</body>
</html>
"""

    return HTMLResponse(content=html_content)


@router.get("/photos/{uuid}/display")
async def serve_display_image(uuid: str, db: Session = Depends(get_db)):
    """Serve the display-size image (max 2400px)."""
    photo = db.query(Photo).filter(Photo.uuid == uuid).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    file_path = settings.display_path / f"{uuid}.jpg"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(file_path, media_type="image/jpeg")


@router.get("/photos/{uuid}/medium")
async def serve_medium_image(uuid: str, db: Session = Depends(get_db)):
    """Serve the medium-size image (max 1400px)."""
    photo = db.query(Photo).filter(Photo.uuid == uuid).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    file_path = settings.storage_path / "photos" / "medium" / f"{uuid}.jpg"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(file_path, media_type="image/jpeg")


@router.get("/photos/{uuid}/thumb")
async def serve_thumbnail(uuid: str, db: Session = Depends(get_db)):
    """Serve the thumbnail image (max 800px)."""
    photo = db.query(Photo).filter(Photo.uuid == uuid).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    file_path = settings.thumb_path / f"{uuid}.jpg"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(file_path, media_type="image/jpeg")
