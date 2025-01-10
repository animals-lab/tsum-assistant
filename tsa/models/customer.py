from typing import Optional, Literal, List
from sqlmodel import Field, SQLModel, Relationship
from tsa.models.catalog import Brand

from enum import Enum


class CustomerGender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class Customer(SQLModel, table=True):
    __tablename__ = "customer"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    gender: CustomerGender | None = None
    age: Optional[int] = None
    description: str = Field(
        default="", description="Free text portrait of the customer"
    )
    style_preferences: str = Field(
        default="", description="Short description of wear style preferences"
    )
    brand_preferences: List["CustomerBrandPreference"] = Relationship(
        back_populates="customer"
    )

    # @property
    # def liked_brand_names(self) -> List[str]:
    #     return [pref.brand_name for pref in self.brand_preferences if pref.preference == "like"]

    # @property
    # def disliked_brand_names(self) -> List[str]:
    #     return [pref.brand_name for pref in self.brand_preferences if pref.preference == "dislike"]


class PreferenceType(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"


class CustomerBrandPreference(SQLModel, table=True):
    __tablename__ = "customer_brand_preference"

    customer_id: Optional[int] = Field(foreign_key="customer.id", primary_key=True)
    brand_name: str = Field(foreign_key="brand.name", primary_key=True)

    preference: PreferenceType = Field(
        description="Customer's preference for the brand"
    )

    customer: Customer = Relationship(back_populates="brand_preferences")
    brand: Brand = Relationship(back_populates="customer_preferences")
