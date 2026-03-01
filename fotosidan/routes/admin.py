import uuid
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from PIL import Image
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import Photo, Tag
from ..config import settings

router = APIRouter()


def _format_exposure_time(value) -> str:
    """Format exposure time as a fraction string like '1/250'."""
    if isinstance(value, float):
        if value >= 1:
            return str(round(value, 1))
        # Convert to fraction
        denominator = round(1 / value)
        return f"1/{denominator}"
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
    return str(value)


def extract_exif_data(image: Image.Image) -> dict:
    """Extract EXIF data from PIL Image object."""
    exif_data = {}
    try:
        exif = image.getexif()
        if not exif:
            return exif_data

        # Merge main IFD and Exif sub-IFD into one lookup dict
        merged = dict(exif)
        exif_ifd = exif.get_ifd(0x8769)  # ExifIFD
        merged.update(exif_ifd)

        # Tags in main IFD
        if 0x010F in merged:
            exif_data["exif_make"] = str(merged[0x010F]).strip()
        if 0x0110 in merged:
            exif_data["exif_model"] = str(merged[0x0110]).strip()

        # DateTimeOriginal (preferred) or DateTime
        if 0x9003 in merged:
            exif_data["exif_datetime_orig"] = str(merged[0x9003])
        elif 0x0132 in merged:
            exif_data["exif_datetime_orig"] = str(merged[0x0132])

        # ExposureTime
        if 0x829A in merged:
            exif_data["exif_exposure_time"] = _format_exposure_time(merged[0x829A])

        # FNumber
        if 0x829D in merged:
            try:
                exif_data["exif_fnumber"] = float(merged[0x829D])
            except (TypeError, ValueError):
                pass

        # ISO
        if 0x8827 in merged:
            try:
                exif_data["exif_iso"] = int(merged[0x8827])
            except (TypeError, ValueError):
                pass

        # FocalLength
        if 0x920A in merged:
            try:
                exif_data["exif_focal_length"] = float(merged[0x920A])
            except (TypeError, ValueError):
                pass

        # FocalLengthIn35mmFilm
        if 0xA405 in merged:
            try:
                exif_data["exif_focal_35mm"] = int(merged[0xA405])
            except (TypeError, ValueError):
                pass

    except Exception:
        pass  # Silently ignore EXIF extraction errors

    return exif_data


def extract_xmp_keywords(file_content: bytes) -> list:
    """Extract Lightroom keywords from XMP metadata in JPEG."""
    keywords = set()

    try:
        # Search for XMP header in JPEG APP1 markers
        xmp_start = file_content.find(b"http://ns.adobe.com/xap/1.0/\x00")
        if xmp_start == -1:
            return list(keywords)

        # Find the start of the XMP segment
        segment_start = xmp_start - 4  # Back up to find segment marker
        if segment_start < 0:
            segment_start = 0

        # Find XML end tag
        xmp_data_start = xmp_start + len(b"http://ns.adobe.com/xap/1.0/\x00")
        xmp_data_end = file_content.find(b"\x00", xmp_data_start)
        if xmp_data_end == -1:
            xmp_data_end = file_content.find(b"</x:xmpmeta>", xmp_data_start) + len(b"</x:xmpmeta>")

        if xmp_data_end > xmp_data_start:
            xmp_xml = file_content[xmp_data_start:xmp_data_end]

            try:
                # Parse XMP XML
                root = ET.fromstring(xmp_xml)

                # Define namespaces
                namespaces = {
                    "dc": "http://purl.org/dc/elements/1.1/",
                    "lr": "http://ns.adobe.com/lightroom/1.0/",
                }

                # Extract flat keywords from dc:subject
                for subject in root.findall(".//dc:subject", namespaces):
                    for bag_item in subject.findall(".//rdf:li", {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"}):
                        if bag_item.text:
                            keywords.add(bag_item.text.strip())

                # Extract hierarchical keywords from lr:hierarchicalSubject
                for hier_subject in root.findall(".//lr:hierarchicalSubject", namespaces):
                    for bag_item in hier_subject.findall(".//rdf:li", {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#"}):
                        if bag_item.text:
                            # Take the leaf (last part) of hierarchy path
                            parts = bag_item.text.strip().split("|")
                            if parts:
                                keywords.add(parts[-1].strip())
            except ET.ParseError:
                pass  # Silently ignore XML parse errors
    except Exception:
        pass  # Silently ignore all XMP extraction errors

    return sorted(list(keywords))


def resize_image(image: Image.Image, max_dimension: int) -> Image.Image:
    """Resize image to fit max_dimension."""
    image.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
    return image


def process_upload(file_content: bytes, filename: str) -> tuple:
    """Process uploaded image: resize and extract metadata."""
    # Generate UUID for filename
    photo_uuid = str(uuid.uuid4())

    # Load image
    img = Image.open(BytesIO(file_content))

    # Extract EXIF data
    exif_data = extract_exif_data(img)

    # Extract XMP keywords
    keywords = extract_xmp_keywords(file_content)

    # Get image dimensions after potential rotation
    width, height = img.size

    # Convert to RGB (handles CMYK, RGBA, etc.)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Save small image (800px for grid view)
    small_img = img.copy()
    small_img.thumbnail((800, 800), Image.LANCZOS)
    small_path = settings.thumb_path / f"{photo_uuid}.jpg"
    small_img.save(str(small_path), format="JPEG", quality=100, progressive=True)

    # Save large image (2400px for list and slideshow)
    large_img = img.copy()
    large_img.thumbnail((2400, 2400), Image.LANCZOS)
    large_width, large_height = large_img.size
    large_path = settings.display_path / f"{photo_uuid}.jpg"
    large_img.save(str(large_path), format="JPEG", quality=100, progressive=True)

    return photo_uuid, large_width, large_height, exif_data, keywords


@router.get("/")
async def admin_index():
    """Redirect to photos dashboard."""
    return RedirectResponse(url="/admin/photos")


@router.get("/photos")
async def dashboard(db: Session = Depends(get_db)):
    """Display admin dashboard with photo list."""
    photos = db.query(Photo).order_by(Photo.sort_order).all()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - {settings.site_title}</title>
    <link rel="stylesheet" href="/static/admin.css">
    <script src="https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js"></script>
    <script src="https://unpkg.com/htmx.org"></script>
</head>
<body>
    <div class="admin-container">
        <a href="/" style="text-decoration: none; color: #999; font-size: 14px; margin-bottom: 20px; display: inline-block;">← back to {settings.site_title}</a>
        <h1>{settings.site_title} Admin</h1>
        <a href="/admin/photos/upload" class="btn btn-primary">Upload Photo</a>

        <h2>Photos</h2>
        <table id="photos-list" class="photos-table">
            <thead>
                <tr>
                    <th>Thumbnail</th>
                    <th>Original Name</th>
                    <th>Title</th>
                    <th>Tags</th>
                    <th>Visible</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="sortable-photos">
"""

    for photo in photos:
        tags_str = ", ".join([t.name for t in photo.tags])
        html += f"""                <tr class="photo-row" data-photo-id="{photo.id}">
                    <td><img src="/photos/{photo.uuid}/thumb" alt="" style="max-width: 100px; max-height: 100px;"></td>
                    <td>{photo.filename_orig}</td>
                    <td>{photo.title or '-'}</td>
                    <td>{tags_str or '-'}</td>
                    <td>
                        <input type="checkbox" {"checked" if photo.visible else ""}
                               hx-post="/admin/photos/{photo.id}?action=toggle_visible"
                               hx-on::after-request="location.reload()">
                    </td>
                    <td>
                        <a href="/admin/photos/{photo.id}" class="btn btn-small">Edit</a>
                        <button hx-delete="/admin/photos/{photo.id}"
                                hx-confirm="Delete this photo?"
                                class="btn btn-small btn-danger">Delete</button>
                    </td>
                </tr>
"""

    html += """            </tbody>
        </table>

        <script>
        const sortable = Sortable.create(document.getElementById('sortable-photos'), {
            onEnd: async () => {
                const order = Array.from(document.querySelectorAll('.photo-row')).map(row => row.dataset.photoId);
                await fetch('/admin/photos/reorder', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({order: order.map(Number)})
                });
            }
        });
        </script>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/photos/upload")
async def upload_form():
    """Display upload form."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload - {settings.site_title}</title>
    <link rel="stylesheet" href="/static/admin.css">
</head>
<body>
    <div class="admin-container">
        <h1>Upload Photo</h1>
        <form method="post" enctype="multipart/form-data" action="/admin/photos/upload">
            <div class="form-group">
                <label for="file">Photo File</label>
                <input type="file" name="file" id="file" required accept="image/jpeg,image/jpg">
            </div>
            <button type="submit" class="btn btn-primary">Upload</button>
            <a href="/admin/photos" class="btn">Cancel</a>
        </form>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html)


@router.post("/photos/upload")
async def handle_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Handle photo upload, EXIF extraction, resizing, and database entry."""
    try:
        # Read file content
        content = await file.read()

        # Check file size
        if len(content) > settings.max_upload_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.max_upload_size // 1024 // 1024}MB"
            )

        # Process the upload
        photo_uuid, width, height, exif_data, keywords = process_upload(content, file.filename)

        # Get max sort_order and increment
        max_order = db.query(func.max(Photo.sort_order)).scalar() or 0

        # Create photo record
        photo = Photo(
            uuid=photo_uuid,
            filename_orig=file.filename,
            width=width,
            height=height,
            sort_order=max_order + 1,
            **exif_data
        )

        db.add(photo)
        db.flush()  # Get the photo ID

        # Add keywords as tags
        for keyword in keywords:
            tag = db.query(Tag).filter(func.lower(Tag.name) == keyword.lower()).first()
            if not tag:
                tag = Tag(name=keyword)
                db.add(tag)
                db.flush()
            photo.tags.append(tag)

        db.commit()

        return RedirectResponse(url=f"/admin/photos/{photo.id}", status_code=303)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/photos/reorder")
async def reorder_photos(request: Request, db: Session = Depends(get_db)):
    """Update photo sort order from drag-and-drop reordering."""
    data = await request.json()
    order = data.get("order", [])

    for sort_order, photo_id in enumerate(order):
        photo = db.query(Photo).filter(Photo.id == photo_id).first()
        if photo:
            photo.sort_order = sort_order

    db.commit()
    return {"status": "ok"}


@router.get("/photos/{photo_id}")
async def photo_detail(photo_id: int, db: Session = Depends(get_db)):
    """Display photo detail and edit form."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Build EXIF table
    exif_fields = [
        ("Make", photo.exif_make),
        ("Model", photo.exif_model),
        ("Date/Time", photo.exif_datetime_orig),
        ("Exposure", photo.exif_exposure_time),
        ("F-Number", photo.exif_fnumber),
        ("ISO", photo.exif_iso),
        ("Focal Length", photo.exif_focal_length),
        ("35mm Equiv.", photo.exif_focal_35mm),
    ]

    exif_html = ""
    for label, value in exif_fields:
        if value:
            exif_html += f"<tr><td>{label}</td><td>{value}</td></tr>"

    # Build tags HTML
    tags_html = ""
    for tag in photo.tags:
        tags_html += f"""<span class="tag-badge">
            {tag.name}
            <button type="button" hx-delete="/admin/photos/{photo.id}/tags/{tag.id}"
                    hx-swap="outerHTML swap:1s" class="tag-remove">×</button>
        </span>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Photo Detail - {settings.site_title}</title>
    <link rel="stylesheet" href="/static/admin.css">
    <script src="https://unpkg.com/htmx.org"></script>
</head>
<body>
    <div class="admin-container">
        <a href="/admin/photos" class="btn">← Back</a>

        <h1>Photo Detail</h1>

        <div class="photo-detail">
            <img src="/photos/{photo.uuid}/display" alt="" style="max-width: 500px; max-height: 500px;">
        </div>

        <form method="post" action="/admin/photos/{photo.id}">
            <div class="form-group">
                <label for="title">Title</label>
                <input type="text" name="title" id="title" value="{photo.title or ''}">
            </div>
            <div class="form-group">
                <label for="description">Description</label>
                <textarea name="description" id="description">{photo.description or ''}</textarea>
            </div>
            <div class="form-group">
                <label for="visible">
                    <input type="checkbox" name="visible" id="visible" {"checked" if photo.visible else ""}>
                    Visible
                </label>
            </div>
            <button type="submit" class="btn btn-primary">Save</button>
        </form>

        <h2>EXIF Data</h2>
        <table class="exif-table">
            <thead>
                <tr><th>Field</th><th>Value</th></tr>
            </thead>
            <tbody>
                {exif_html if exif_html else '<tr><td colspan="2">No EXIF data</td></tr>'}
            </tbody>
        </table>

        <h2>Tags</h2>
        <div id="tags-container" class="tags-container">
            {tags_html if tags_html else '<p>No tags</p>'}
        </div>

        <form id="tag-form" hx-post="/admin/photos/{photo.id}/tags" hx-target="#tags-container" hx-swap="innerHTML">
            <div class="form-group">
                <label for="new-tag">Add Tag</label>
                <input type="text" name="tag_name" id="new-tag" placeholder="Enter tag name" required>
                <button type="submit" class="btn btn-small">Add</button>
            </div>
        </form>
        <script>
        document.getElementById('tag-form').addEventListener('htmx:afterSwap', function() {{
            document.getElementById('new-tag').value = '';
            document.getElementById('new-tag').focus();
        }});
        </script>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html)


@router.post("/photos/{photo_id}")
async def update_photo(photo_id: int, request: Request, db: Session = Depends(get_db)):
    """Update photo title, description, and visibility."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    form_data = await request.form()

    # Check for toggle_visible action (from visibility checkbox)
    action = request.query_params.get("action")
    if action == "toggle_visible":
        photo.visible = not photo.visible
        db.commit()
        return {"status": "ok"}

    # Update fields
    photo.title = form_data.get("title") or None
    photo.description = form_data.get("description") or None
    photo.visible = "visible" in form_data

    db.commit()
    return RedirectResponse(url=f"/admin/photos/{photo_id}", status_code=303)


@router.delete("/photos/{photo_id}")
async def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    """Delete a photo and its files."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # Delete image files
    thumb_path = settings.thumb_path / f"{photo.uuid}.jpg"
    display_path = settings.display_path / f"{photo.uuid}.jpg"

    if thumb_path.exists():
        thumb_path.unlink()
    if display_path.exists():
        display_path.unlink()

    # Delete from database
    db.delete(photo)
    db.commit()

    return {"status": "deleted"}


@router.post("/photos/{photo_id}/tags")
async def add_tag(photo_id: int, request: Request, db: Session = Depends(get_db)):
    """Add a tag to a photo."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    form_data = await request.form()
    tag_name = form_data.get("tag_name", "").strip()

    if not tag_name:
        raise HTTPException(status_code=400, detail="Tag name required")

    # Get or create tag
    tag = db.query(Tag).filter(func.lower(Tag.name) == tag_name.lower()).first()
    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        db.flush()

    # Add to photo if not already present
    if tag not in photo.tags:
        photo.tags.append(tag)
        db.commit()

    # Return updated tags HTML
    tags_html = ""
    for t in photo.tags:
        tags_html += f"""<span class="tag-badge">
            {t.name}
            <button type="button" hx-delete="/admin/photos/{photo.id}/tags/{t.id}"
                    hx-swap="outerHTML swap:1s" class="tag-remove">×</button>
        </span>
"""

    return HTMLResponse(content=tags_html)


@router.delete("/photos/{photo_id}/tags/{tag_id}")
async def remove_tag(photo_id: int, tag_id: int, db: Session = Depends(get_db)):
    """Remove a tag from a photo."""
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if tag in photo.tags:
        photo.tags.remove(tag)
        db.commit()

    return ""
