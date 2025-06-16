from sqlalchemy import Table, Column, ForeignKey, String
from src.cores.database import Base

post_category = Table(
    "post_category",
    Base.metadata,
    Column(
        "post_id",
        String(36),
        ForeignKey("posts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "category_id",
        String(36),
        ForeignKey("categories.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
