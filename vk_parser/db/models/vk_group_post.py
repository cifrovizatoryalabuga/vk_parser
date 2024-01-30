from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from vk_parser.db.models.base import Base, TimestampMixin


class VkGroupPost(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    vk_group_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("vk_group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    posted_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(String, nullable=False)
    user_vk_ids: Mapped[Sequence[int]] = mapped_column(
        ARRAY(BigInteger, as_tuple=True),
        nullable=False,
        server_default="{ }",
    )
