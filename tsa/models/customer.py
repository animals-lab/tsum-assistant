from typing import Optional, Literal, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum
from sqlalchemy import ARRAY, String, Column

from tsa.models.catalog import Brand


class CustomerGender(str, Enum):
    MALE = "male"
    FEMALE = "female"

    @classmethod
    def from_literal(cls, literal: str) -> "CustomerGender":
        if "мужской" in literal.lower():
            return cls.MALE
        elif "женский" in literal.lower():
            return cls.FEMALE
        else:
            return None
        
    def to_literal(self) -> str:
        return {
            CustomerGender.MALE: "мужской",
            CustomerGender.FEMALE: "женский",
        }.get(self)


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
        back_populates="customer", sa_relationship_kwargs={"lazy": "selectin"}
    )

    segments: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    price_segments: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))

    @property
    def liked_brand_names(self) -> List[str]:
        return [
            pref.brand_name
            for pref in self.brand_preferences
            if pref.preference == "like"
        ]

    @property
    def disliked_brand_names(self) -> List[str]:
        return [
            pref.brand_name
            for pref in self.brand_preferences
            if pref.preference == "dislike"
        ]

    @property
    def gender_literal(self) -> str | None:
        # @TODO: remove this and unify catalog and chat
        return {
            CustomerGender.MALE: "Мужской",
            CustomerGender.FEMALE: "Женский",
        }.get(self.gender, None)

    @property
    def prompt(self) -> str:
        # @TODO: organize prompts in a separate file
        parts = []
        if self.name:
            parts.append(f"Name: {self.name}")
        if self.gender:
            parts.append(
                f"Gender: {self.gender.name}"
            )
        if self.liked_brand_names:
            parts.append(
                f"Liked brands: {'; '.join(self.liked_brand_names)}"
            )
        if self.disliked_brand_names:
            parts.append(
                f"Disliked brands: {'; '.join(self.disliked_brand_names)}"
            )
        if self.style_preferences:
            parts.append(f"Style preferences: {self.style_preferences}")
        if self.description:
            parts.append(f"Description: {self.description}")


        return "\n".join(parts)


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
