from data.db import Ticket, async_session
from sqlalchemy import select, delete


async def get_tickets(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Ticket).where(Ticket.user_id == user_id))
        return result.scalars().all()


async def add_ticket(user_id: int, from_city: str, to_city: str, date: str):
    async with async_session() as session:
        ticket = Ticket(
            user_id=user_id,
            from_city=from_city,
            to_city=to_city,
            date=date
        )
        session.add(ticket)
        await session.commit()


async def delete_ticket(ticket_id: int):
    async with async_session() as session:
        await session.execute(delete(Ticket).where(Ticket.id == ticket_id))
        await session.commit()
