from data.db import TrackedTicket, async_session
from sqlalchemy import select, delete


async def get_tracked(user_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(TrackedTicket).where(TrackedTicket.user_id == user_id)
        )
        return result.scalars().all()


async def add_tracked(user_id: int, from_city: str, to_city: str, date_from: str, 
                     date_to: str, baggage: str, transfers: str, price_limit: str):
    async with async_session() as session:
        ticket = TrackedTicket(
            user_id=user_id,
            from_city=from_city,
            to_city=to_city,
            date_from=date_from,
            date_to=date_to,
            baggage=baggage,
            transfers=transfers,
            price_limit=price_limit,
        )
        session.add(ticket)
        await session.commit()


async def delete_tracked(ticket_id: int):
    async with async_session() as session:
        await session.execute(delete(TrackedTicket).where(TrackedTicket.id == ticket_id))
        await session.commit()
