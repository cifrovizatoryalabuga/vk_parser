from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from vk_parser.db.models.base import Base, TimestampMixin


class VkGroup(TimestampMixin, Base):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    parser_request_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("parser_request.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vk_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
