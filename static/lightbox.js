let currentIndex = 0;
const photos = Array.from(document.querySelectorAll('.photo-item img')).map(img => {
    const match = img.src.match(/\/photos\/([^/]+)\//);
    return match ? match[1] : null;
}).filter(Boolean);
const totalPhotos = photos.length;
let selectedTags = new Set();

function showGrid2() {
    const gallery = document.getElementById('gallery-container');
    gallery.classList.add('active');
    gallery.classList.add('grid-2');
    gallery.classList.remove('grid-1');
    document.getElementById('slideshow-container').classList.remove('active');
    document.getElementById('grid-2-btn').classList.add('active');
    document.getElementById('grid-1-btn').classList.remove('active');
    document.getElementById('slideshow-btn').classList.remove('active');
    document.getElementById('tags-btn').classList.remove('active');
}

function showGrid1() {
    const gallery = document.getElementById('gallery-container');
    gallery.classList.add('active');
    gallery.classList.add('grid-1');
    gallery.classList.remove('grid-2');
    document.getElementById('slideshow-container').classList.remove('active');
    document.getElementById('grid-1-btn').classList.add('active');
    document.getElementById('grid-2-btn').classList.remove('active');
    document.getElementById('slideshow-btn').classList.remove('active');
    document.getElementById('tags-btn').classList.remove('active');
}

function showSlideshow(index = 0) {
    currentIndex = index;
    document.getElementById('gallery-container').classList.remove('active');
    document.getElementById('slideshow-container').classList.add('active');
    document.getElementById('grid-2-btn').classList.remove('active');
    document.getElementById('grid-1-btn').classList.remove('active');
    document.getElementById('slideshow-btn').classList.add('active');
    document.getElementById('tags-btn').classList.remove('active');
    updateSlide();
    updateButtonVisibility();
}

function toggleTagsDropdown() {
    const dropdown = document.querySelector('.tags-dropdown');
    const tagsBtn = document.getElementById('tags-btn');
    if (dropdown) {
        dropdown.classList.toggle('active');
        // Position dropdown under the Tags button
        if (dropdown.classList.contains('active')) {
            const btnRect = tagsBtn.getBoundingClientRect();
            const controlsRect = tagsBtn.closest('.controls').getBoundingClientRect();
            const relativeLeft = btnRect.left - controlsRect.left;
            dropdown.style.left = relativeLeft + 'px';
        }
    }
}

function filterPhotos() {
    // Filter gallery items
    document.querySelectorAll('.photo-item').forEach(item => {
        if (selectedTags.size === 0) {
            item.style.display = '';
        } else {
            const itemTags = item.dataset.tags ? item.dataset.tags.split(',').map(t => t.trim()) : [];
            const hasAllTags = Array.from(selectedTags).every(tag => itemTags.includes(tag));
            item.style.display = hasAllTags ? '' : 'none';
        }
    });

    // Filter slideshow items and mark hidden ones
    document.querySelectorAll('.slideshow-item').forEach(item => {
        if (selectedTags.size === 0) {
            item.dataset.filtered = '';
        } else {
            const itemTags = item.dataset.tags ? item.dataset.tags.split(',').map(t => t.trim()) : [];
            const hasAllTags = Array.from(selectedTags).every(tag => itemTags.includes(tag));
            item.dataset.filtered = hasAllTags ? '' : 'hidden';
        }
    });

    // If current slide is now hidden, jump to first visible
    updateSlide();
    updateButtonVisibility();
}

function nextSlide() {
    const slideshowItems = document.querySelectorAll('.slideshow-item');
    const visibleItems = Array.from(slideshowItems).filter(item => item.dataset.filtered !== 'hidden');
    const currentVisibleIndex = visibleItems.findIndex(item => parseInt(item.dataset.index) === currentIndex);

    // Don't navigate if already on last visible slide
    if (currentVisibleIndex >= visibleItems.length - 1) {
        updateButtonVisibility();
        return;
    }

    let nextIndex = (currentIndex + 1) % totalPhotos;
    while (slideshowItems[nextIndex].dataset.filtered === 'hidden' && nextIndex !== currentIndex) {
        nextIndex = (nextIndex + 1) % totalPhotos;
    }
    currentIndex = nextIndex;
    updateSlide();
}

function prevSlide() {
    const slideshowItems = document.querySelectorAll('.slideshow-item');
    const visibleItems = Array.from(slideshowItems).filter(item => item.dataset.filtered !== 'hidden');
    const currentVisibleIndex = visibleItems.findIndex(item => parseInt(item.dataset.index) === currentIndex);

    // Don't navigate if already on first visible slide
    if (currentVisibleIndex <= 0) {
        updateButtonVisibility();
        return;
    }

    let prevIndex = (currentIndex - 1 + totalPhotos) % totalPhotos;
    while (slideshowItems[prevIndex].dataset.filtered === 'hidden' && prevIndex !== currentIndex) {
        prevIndex = (prevIndex - 1 + totalPhotos) % totalPhotos;
    }
    currentIndex = prevIndex;
    updateSlide();
}

function updateSlide() {
    const slideshowItems = document.querySelectorAll('.slideshow-item');

    // If current item is hidden, find first visible item
    if (slideshowItems[currentIndex].dataset.filtered === 'hidden') {
        let foundVisible = false;
        for (let i = 0; i < totalPhotos; i++) {
            if (slideshowItems[i].dataset.filtered !== 'hidden') {
                currentIndex = i;
                foundVisible = true;
                break;
            }
        }
        if (!foundVisible) {
            // All items are hidden, show the current one anyway
            currentIndex = 0;
        }
    }

    slideshowItems.forEach((item, i) => {
        item.style.display = i === currentIndex ? 'block' : 'none';
    });

    updateButtonVisibility();
}

function updateButtonVisibility() {
    const slideshowItems = document.querySelectorAll('.slideshow-item');
    const visibleItems = Array.from(slideshowItems).filter(item => item.dataset.filtered !== 'hidden');

    // Find the currently visible slideshow item
    const currentItem = document.querySelector('.slideshow-item[style*="display: block"]');
    if (!currentItem) return;

    // Get buttons from the currently visible item only
    const buttons = currentItem.querySelectorAll('.slideshow-controls button');
    const prevBtn = buttons[0];
    const nextBtn = buttons[1];

    if (prevBtn && nextBtn) {
        const currentVisibleIndex = visibleItems.findIndex(item => parseInt(item.dataset.index) === currentIndex);

        // Hide prev if on first visible slide
        prevBtn.style.display = currentVisibleIndex === 0 ? 'none' : 'block';

        // Hide next if on last visible slide
        nextBtn.style.display = currentVisibleIndex === visibleItems.length - 1 ? 'none' : 'block';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Initialize data-filtered attribute on all slideshow items
    document.querySelectorAll('.slideshow-item').forEach(item => {
        if (!item.dataset.filtered) {
            item.dataset.filtered = '';
        }
    });

    const lightbox = document.getElementById('lightbox');
    const lightboxImage = lightbox ? lightbox.querySelector('img') : null;
    let lightboxIndex = 0;

    if (lightbox) {
        lightbox.addEventListener('click', () => {
            lightbox.classList.remove('active');
        });

        const prev = lightbox.querySelector('.lightbox-prev');
        const next = lightbox.querySelector('.lightbox-next');

        if (prev) prev.addEventListener('click', (e) => {
            e.stopPropagation();
            lightboxIndex = (lightboxIndex - 1 + photos.length) % photos.length;
            lightboxImage.src = `/photos/${photos[lightboxIndex]}/display`;
        });

        if (next) next.addEventListener('click', (e) => {
            e.stopPropagation();
            lightboxIndex = (lightboxIndex + 1) % photos.length;
            lightboxImage.src = `/photos/${photos[lightboxIndex]}/display`;
        });

        document.addEventListener('keydown', (e) => {
            if (!lightbox.classList.contains('active')) return;
            if (e.key === 'Escape') lightbox.classList.remove('active');
            if (e.key === 'ArrowLeft') {
                lightboxIndex = (lightboxIndex - 1 + photos.length) % photos.length;
                lightboxImage.src = `/photos/${photos[lightboxIndex]}/display`;
            }
            if (e.key === 'ArrowRight') {
                lightboxIndex = (lightboxIndex + 1) % photos.length;
                lightboxImage.src = `/photos/${photos[lightboxIndex]}/display`;
            }
        });
    }

    // Add click handlers to photo images to redirect to slideshow
    document.querySelectorAll('.photo-item img').forEach((img) => {
        img.style.cursor = 'pointer';
        img.addEventListener('click', () => {
            // Only redirect to slideshow if Tags view is not active
            if (!document.getElementById('tags-btn').classList.contains('active')) {
                const index = Array.from(document.querySelectorAll('.photo-item')).indexOf(img.closest('.photo-item'));
                showSlideshow(index);
            }
        });
    });

    // Helper function to handle tag toggling
    const handleTagClick = (tagName) => {
        if (selectedTags.has(tagName)) {
            selectedTags.delete(tagName);
        } else {
            selectedTags.add(tagName);
        }

        // Update active state for all matching tags
        document.querySelectorAll('.photo-tag, .dropdown-tag').forEach(t => {
            const tName = t.textContent.toLowerCase();
            if (selectedTags.has(tName)) {
                t.classList.add('active');
            } else {
                t.classList.remove('active');
            }
        });

        filterPhotos();
    };

    // Add tag click handlers for photo tags
    document.querySelectorAll('.photo-tag').forEach(tag => {
        tag.addEventListener('click', (e) => {
            e.stopPropagation();
            handleTagClick(tag.textContent.toLowerCase());
        });
    });

    // Add tag click handlers for dropdown tags
    document.querySelectorAll('.dropdown-tag').forEach(tag => {
        tag.addEventListener('click', (e) => {
            e.stopPropagation();
            handleTagClick(tag.getAttribute('data-tag-name'));
        });
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        const dropdown = document.querySelector('.tags-dropdown');
        const tagsBtn = document.getElementById('tags-btn');
        if (dropdown && !dropdown.contains(e.target) && !tagsBtn.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    });
});
