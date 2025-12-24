from models.data.db import UserFilters, async_session
from sqlalchemy import select


async def get_filters(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(UserFilters).where(UserFilters.user_id == user_id))
        filters = result.scalars().first()

        if filters is None:
            filters = UserFilters(user_id=user_id)
            session.add(filters)
            await session.commit()

        return filters


async def update_filter(user_id: int, field: str, value: str):
    async with async_session() as session:
        filters = await get_filters(user_id)
        setattr(filters, field, value)
        session.add(filters)
        await session.commit()


async def clear_filter(user_id: int, field: str):
    async with async_session() as session:
        filters = await get_filters(user_id)
        setattr(filters, field, "")
        session.add(filters)
        await session.commit()
