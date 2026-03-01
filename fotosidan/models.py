from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, Table
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship
photo_tags = Table(
    "photo_tags",
    Base.metadata,
    Column("photo_id", Integer, ForeignKey("photos.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Photo(Base):
    """Photo model."""
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String, unique=True, nullable=False)
    filename_orig = Column(String, nullable=False)
    title = Column(String)
    description = Column(Text)
    sort_order = Column(Integer, nullable=False, default=0)
    visible = Column(Boolean, nullable=False, default=True)
    width = Column(Integer)
    height = Column(Integer)
    exif_make = Column(String)
    exif_model = Column(String)
    exif_datetime_orig = Column(String)
    exif_exposure_time = Column(String)
    exif_fnumber = Column(Float)
    exif_iso = Column(Integer)
    exif_focal_length = Column(Float)
    exif_focal_35mm = Column(Integer)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    tags = relationship("Tag", secondary=photo_tags, back_populates="photos")


class Tag(Base):
    """Tag model."""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    photos = relationship("Photo", secondary=photo_tags, back_populates="tags")
