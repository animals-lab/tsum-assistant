from sqlmodel import SQLModel
from tsa.config import settings
from tsa.models.catalog import Brand
from tsa.models.customer import Customer#, CustomerBrandPreference
import asyncio

async def create_tables():
    async with settings.db.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(create_tables())
