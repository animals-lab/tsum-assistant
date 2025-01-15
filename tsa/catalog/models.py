import hashlib
import json
from uuid import UUID
from functools import cache
from typing import Any, Callable, Dict, List, Literal, Optional, TypeVar
from xml.etree import ElementTree as ET

from pydantic import BaseModel, Field

GenderType = Literal["Мужской", "Женский", "Детский"]
T = TypeVar("T")


def get_category_tree(category_id: str, categories: Dict[str, dict]) -> list[dict]:
    """
    Get all parent categories for a given category ID, starting from the root.

    Args:
        category_id: ID of the category to get parents for
        categories: Dictionary of all categories

    Returns:
        list: List of category dictionaries from root to the given category
    """

    @cache
    def get_parent_categories(current_id: str) -> list[dict]:
        if not current_id or current_id not in categories:
            return []

        current_category = categories[current_id]
        if not current_category:
            return []

        category = {
            "id": current_id,
            "name": current_category["name"],
            "url": current_category["url"],
        }

        parent_id = current_category.get("parent_id")
        if parent_id:
            return get_parent_categories(str(parent_id)) + [category]
        return [category]

    return get_parent_categories(category_id)


class Offer(BaseModel):
    """Pydantic model representing a product offer from the catalog"""

    # Required fields
    id: str  # acutally uuid, but it's a string so we dont mess with json  encoding for now
    tsum_sku: str  # yes, it's a string, not int
    vendor_sku: Optional[str] = None

    name: str

    # Optional basic fields
    available: bool = True
    price: Optional[int] = None
    old_price: Optional[int] = None
    # currency: Optional[str] = None
    # category_id: Optional[int] = None
    vendor: Optional[str] = None

    picture: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None

    # Extracted from params
    color: Optional[str] = None
    color_shade: Optional[str] = None
    design_country: Optional[str] = None
    gender: Optional[GenderType] = None
    season: Optional[str] = None
    material: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    has_discount: Optional[bool] = None

    hash: Optional[str] = None
    # Remaining parameters
    # params: Dict[str, Optional[str]] = Field(default_factory=dict)

    def to_text(self) -> str:
        """Create rich text description of the offer"""
        lines = []

        if self.name:
            lines.append(self.name)
        if self.vendor:
            lines.append(self.vendor)
        if self.description:
            lines.append(self.description)

        # if self.material:
        #     lines.append(self.material)

        if self.design_country:
            lines.append(self.design_country)

        return "\n".join(lines)

    @staticmethod
    def from_xml_element(elem: ET.Element, categories: Dict[str, dict]) -> "Offer":
        """Convert XML element to Offer instance"""

        def extract_value(
            elem: ET.Element, tag: str, converter: Callable[[str], T] = str
        ) -> Optional[T]:
            """Extract value from XML element with optional type conversion"""
            element = elem.find(tag)
            if element is not None and element.text:
                return converter(element.text)
            return None

        # Field mappings for parameters
        param_field_mapping = {
            "Цвет": "color",
            "Оттенок": "color_shade",
            "Страна дизайна": "design_country",
            "Пол": "gender",
            "Сезон": "season",
            "Материал": "material",
            "custom categories": "category",
            "Артикул": "tsum_sku",
            "Скидка": "discount",
        }
        basic_data = {
            "vendor_sku": extract_value(elem, "vendorCode"),
            "available": elem.get("available") == "true",
            "price": extract_value(elem, "price", lambda x: int(float(x))),
            "old_price": extract_value(elem, "oldprice", lambda x: int(float(x))),
            # "currency": extract_value(elem, "currencyId"),
            "category_id": extract_value(elem, "categoryId", int),
            "name": extract_value(elem, "name"),
            "vendor": extract_value(elem, "vendor"),
            "picture": extract_value(elem, "picture"),
            "description": extract_value(elem, "description"),
            "url": extract_value(elem, "url"),
        }
        basic_data["id"] = str(UUID(int=int(elem.get("id"))))
        # Process parameters
        special_fields = {}
        params = {}

        for param in elem.findall("param"):
            param_name = param.get("name")
            param_value = param.text

            if param_name in param_field_mapping:
                special_fields[param_field_mapping[param_name]] = param_value
            # else:
            #     params[param_name] = param_value

        # Combine all data
        basic_data.update(special_fields)
        cat_tree = get_category_tree(basic_data["category_id"], categories)

        # Combine categories from hierarchy and custom categories parameter
        categories_from_tree = [cat["name"] for cat in cat_tree]
        categories_from_param = (
            basic_data.get("category", "").split(",")
            if basic_data.get("category")
            else []
        )
        basic_data["categories"] = sorted(
            set(categories_from_tree + categories_from_param)
        )

        if basic_data.get("discount") == "Да":
            basic_data["has_discount"] = True
        basic_data["params"] = params

        # hash_data = basic_data  # {k: v for k, v in basic_data.items() if k not in ["available"]}
        offer = Offer(**basic_data)
        offer.hash = hashlib.md5(str(offer.model_dump_json()).encode()).hexdigest()

        return Offer(**basic_data)


class CatalogQueryResponse(BaseModel):
    items: List[Offer]
    scores: List[float]


from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class StructuredQuery(BaseModel):
    brands: Optional[List[str]] = Field(
        None, description='List of brand names (e.g., "Gucci", "Dsquared2").'
    )
    blocked_brands: Optional[List[str]] = Field(
        None, description='List of brand names to exclude (e.g., "EA7", "Off-White").'
    )
    categories: Optional[List[str]] = Field(
        None,
        description='List of product categories in Russian, plural (e.g., "Платья", "Вечерние платья", "Блузки", "Кеды").',
    )
    colors: Optional[List[str]] = Field(
        None, description='List of colors (e.g., "Чёрный", "Белый", "Красный").'
    )
    gender: Optional[GenderType] = Field(
        None, description='Gender category ("Мужской", "Женский").'
    )
    min_price: Optional[float] = Field(None, description="Minimum price filter.")
    max_price: Optional[float] = Field(None, description="Maximum price filter.")
    materials: Optional[List[str]] = Field(
        None, description='List of materials (e.g., "Хлопок", "Шерсть", "Кашемир").'
    )
    query_text: Optional[str] = Field(
        None,
        description='Free-form text query (e.g., "элегантное и легкое", "в клеточку", "в стиле олдмани", "с красной аппликацией"). Include only details not mentioned in other fields.',
    )
    has_discount: Optional[bool] = Field(
        None, description="Whether the product has a discount."
    )

    # complete: bool = Field(
    #     False, description="Must be set to true by agent when it creates a query!"
    # )
    # needed for streaming

    def to_short_description(self) -> str:
        """Creates a short text description of the query, including only set fields."""
        parts = []
        
        if self.brands:
            parts.append(f"бренды: {', '.join(self.brands)}")
        if self.blocked_brands:
            parts.append(f"исключая бренды: {', '.join(self.blocked_brands)}")
        if self.categories:
            parts.append(f"категории: {', '.join(self.categories)}")
        if self.colors:
            parts.append(f"цвета: {', '.join(self.colors)}")
        if self.gender:
            parts.append(f"пол: {self.gender}")
        if self.min_price is not None:
            parts.append(f"цена от {self.min_price}")
        if self.max_price is not None:
            parts.append(f"цена до {self.max_price}")
        if self.materials:
            parts.append(f"материалы: {', '.join(self.materials)}")
        if self.query_text:
            parts.append(f"поиск: {self.query_text}")
        if self.has_discount is not None:
            parts.append("со скидкой" if self.has_discount else "без скидки")
            
        return "; ".join(parts) if parts else ""
        