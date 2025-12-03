from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
import asyncio


# ---------------------------------------------------
# БАЗА
# ---------------------------------------------------
DATABASE_URL = "sqlite+aiosqlite:///tickets.db"


engine = create_async_engine(DATABASE_URL, echo=False)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------
# МОДЕЛЬ: БИЛЕТ
# ---------------------------------------------------
class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer)
    from_city: Mapped[str] = mapped_column(String)
    to_city: Mapped[str] = mapped_column(String)
    date: Mapped[str] = mapped_column(String)


class TrackedTicket(Base):
    __tablename__ = "tracked_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer)

    from_city: Mapped[str] = mapped_column(String)
    to_city: Mapped[str] = mapped_column(String)

    # даты могут быть форматом: одна дата ИЛИ две даты (туда-обратно)
    date_from: Mapped[str] = mapped_column(String)
    date_to: Mapped[str] = mapped_column(String, default="")  # пусто для one-way

    baggage: Mapped[str] = mapped_column(String)
    transfers: Mapped[str] = mapped_column(String)
    price_limit: Mapped[str] = mapped_column(String)


class UserFilters(Base):
    __tablename__ = "user_filters"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    from_city: Mapped[str] = mapped_column(String, default="")
    baggage: Mapped[str] = mapped_column(String, default="")
    transfers: Mapped[str] = mapped_column(String, default="")
    price_limit: Mapped[str] = mapped_column(String, default="")


# ---------------------------------------------------
# СОЗДАНИЕ ТАБЛИЦ
# ---------------------------------------------------
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Для ручного запуска
if __name__ == "__main__":
    asyncio.run(init_db())
