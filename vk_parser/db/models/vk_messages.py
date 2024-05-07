from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from vk_parser.db.models.base import Base, TimestampMixin
from vk_parser.db.utils import make_pg_enum
from vk_parser.generals.enums import VkDialogsStatus


class VkDialogs(TimestampMixin, Base):
    """Диалоги с пользователям в ВК"""

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
    status: Mapped[VkDialogsStatus] = mapped_column(
        make_pg_enum(
            VkDialogsStatus,
            schema=None,
        ),
        nullable=False,
        server_default=VkDialogsStatus.PROCESSING.value,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(),
        nullable=True,
    )


class VkMessages(TimestampMixin, Base):
    """Отправленные сообщения пользователям в ВК"""

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    dialog_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("vk_dialogs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
