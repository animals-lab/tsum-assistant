from typing import List, TYPE_CHECKING, Optional
from sqlmodel import Field, SQLModel, Relationship, Session, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import exists

if TYPE_CHECKING:
    from tsa.models.customer import CustomerBrandPreference, CustomerGender


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

    @classmethod
    async def similar_brand_names(cls, session: AsyncSession, brand_names: str, gender: "CustomerGender") -> List[str]:
        from tsa.models.customer import CustomerGender
    
        if gender == CustomerGender.MALE:
            fields = [cls.segment_male, cls.price_segment_male]
        else:
            fields = [cls.segment_female, cls.price_segment_female]
        
        # TODO: fix this
        result = await session.execute(select(*fields).where(cls.name.in_(brand_names)))
        segments, price_segments = zip(*result.all())
        segments = { s for s in segments if s is not None }
        price_segments = { s for s in price_segments if s is not None }

        stmt = select(cls.name)
        if gender == CustomerGender.MALE: 
            if segments:
                stmt = stmt.where(cls.segment_male.in_(segments))
            if price_segments:
                stmt = stmt.where(cls.price_segment_male.in_(price_segments))
        else:
            if segments:
                stmt = stmt.where(cls.segment_female.in_(segments))
            if price_segments:
                stmt = stmt.where(cls.price_segment_female.in_(price_segments))


        res = await session.scalars(stmt)
        return res.all()


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

