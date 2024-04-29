from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from vk_parser.db.models.base import Base, TimestampMixin


class VkMessages(TimestampMixin, Base):
    """Отправленные сообщения пользователям в ВК"""

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    send_account_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("send_accounts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    vk_group_user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("vk_group_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vk_message_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    vk_conversation_message_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    error_status: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )
