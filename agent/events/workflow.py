from llama_index.core.workflow import Event
from app.catalog.models import StructuredQuery


class ProcessInputRequestEvent(Event):
    user_msg: str


class ProcessInputResultEvent(Event): ...


class CatalogResponseEvent(Event):
    catalog_summary: str


class CatalogRequestEvent(Event):
    structured_query: StructuredQuery


class FashionTrendsRequestEvent(Event):
    query: str


class FashionTrendsResponseEvent(Event):
    response: str
