from typing import List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from tsa.models.customer import CustomerBrandPreference


class Brand(SQLModel, table=True):
    __tablename__ = "brand"
    
    name: str = Field(primary_key=True, description="Brand name")
    customer_preferences: List["CustomerBrandPreference"] = Relationship(
        back_populates="brand"
    )
