from typing import List, TYPE_CHECKING, Optional
from sqlmodel import Field, SQLModel, Relationship, Session, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exists

if TYPE_CHECKING:
    from tsa.models.customer import CustomerBrandPreference


class Brand(SQLModel, table=True):
    __tablename__ = "brand"
    
    name: str = Field(primary_key=True, description="Brand name")
    customer_preferences: List["CustomerBrandPreference"] = Relationship(
        back_populates="brand"
    )

    segment_male: str | None = None
    price_segment_male: str | None = None

    segment_female: str | None = None
    price_segment_female: str | None = None

class Category(SQLModel, table=True):
    __tablename__ = "category"

    id: Optional[int] = Field(primary_key=True, description="Category id")
    parent_id: Optional[int] = Field(description="Parent category id", foreign_key="category.id", default=None, nullable=True)
   
    name: str = Field(description="Category name")
    url: str = Field(description="Category URL")

    children: List["Category"] = Relationship(back_populates="parent")
    parent: Optional["Category"] = Relationship(back_populates="children", sa_relationship_kwargs={"remote_side": "Category.id"})


    @classmethod
    async def exists_by_name(cls, session: AsyncSession, name: str) -> bool:
        statement = select(exists().where(cls.name == name))
        result = await session.scalar(statement)
        return bool(result)

