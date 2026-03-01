#!/usr/bin/env python3
"""Regenerate medium-size (1400px) images for all existing photos."""
import sys
from pathlib import Path
from PIL import Image

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fotosidan.config import settings

def regenerate_medium_images():
    """Generate 1400px medium images from existing display images."""
    display_path = settings.display_path
    medium_path = settings.storage_path / "photos" / "medium"

    # Create medium directory
    medium_path.mkdir(parents=True, exist_ok=True)

    # Find all display images
    display_images = list(display_path.glob("*.jpg"))

    if not display_images:
        print("No display images found.")
        return

    print(f"Found {len(display_images)} photos to process...")

    for i, display_file in enumerate(display_images, 1):
        uuid = display_file.stem
        medium_file = medium_path / f"{uuid}.jpg"

        # Skip if medium already exists
        if medium_file.exists():
            print(f"[{i}/{len(display_images)}] {uuid} - medium already exists, skipping")
            continue

        try:
            # Load and resize
            img = Image.open(display_file)
            img.thumbnail((1400, 1400), Image.LANCZOS)

            # Save medium image
            img.save(str(medium_file), format="JPEG", quality=100, progressive=True)
            print(f"[{i}/{len(display_images)}] {uuid} - generated medium image")
        except Exception as e:
            print(f"[{i}/{len(display_images)}] {uuid} - ERROR: {e}")

    print("Done!")

if __name__ == "__main__":
    regenerate_medium_images()
