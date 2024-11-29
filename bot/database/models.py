from database.connection import Base
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"
    id = None
    telegram_id: Mapped[str] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str]
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_active_conversation: Mapped[bool] = mapped_column(default=True)
    is_banned: Mapped[bool] = mapped_column(default=False)

    histories: Mapped[list["History"]] = relationship(back_populates="user")

    def __str__(self):
        return f"User ({self.telegram_id}, {self.full_name})"


class Chat(Base):
    __tablename__ = "chats"
    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    type: Mapped[str] = mapped_column(String(32))

    histories: Mapped[list["History"]] = relationship(back_populates="chat")

    @property
    def message_count(self):
        return len(self.histories)


class History(Base):
    __tablename__ = "histories"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.telegram_id"))
    user: Mapped["User"] = relationship(back_populates="histories")
    chat_id: Mapped[str] = mapped_column(ForeignKey("chats.id"))
    chat: Mapped["Chat"] = relationship(back_populates="histories")
    command: Mapped[str] = mapped_column(String(255), nullable=True)

    @property
    def name(self):
        return self.user.full_name
