from typing import Annotated, AsyncGenerator
from fastapi import Cookie, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from tsa.models.customer import Customer
from tsa.config import settings
from loguru import logger


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with settings.db.async_session_maker() as session:
        yield session


async def get_current_customer(
    customerId: Annotated[str | None, Cookie(name="customerId")] = None,
    session: AsyncSession = Depends(get_session),
) -> Customer | None:
    logger.info(f"CustomerId cookie value: {customerId}")
    if not customerId:
        return None

    customer = await session.get(Customer, int(customerId))
    return customer
