from llama_index.core.workflow import Event
from tsa.catalog.models import StructuredQuery


class ProcessInputRequestEvent(Event):
    user_msg: str


class ProcessInputResultEvent(Event): ...


class CatalogResponseEvent(Event):
    catalog_summary: str | None


class CatalogRequestEvent(Event):
    structured_query: StructuredQuery


class FashionTrendsRequestEvent(Event):
    query: str


class FashionTrendsResponseEvent(Event):
    response: str


##################
from enum import Enum
from typing import List, Optional

from llama_index.core.workflow import Event
from tsa.catalog.models import Offer


class AgentRunEventType(Enum):
    TEXT = "text"
    PROGRESS = "progress"


class ProgressEvent(Event):
    msg: str


class AgentRunEvent(Event):
    name: str
    msg: str
    event_type: AgentRunEventType = AgentRunEventType.TEXT
    data: Optional[dict] = None

    def to_annotation(self) -> dict:
        # TODO UGLY!
        agent_human_names = {
            "main": "Ассистент",
            "TransferToAgent": "Координатор",
            "query_catalog_tool": "Поиск в каталоге",
            "fetch_fashion_trends": "Эксперт по стилю",
        }

        return {
            "type": "agent",
            "data": {
                "agent": agent_human_names.get(self.name, self.name),
                "type": self.event_type.value,
                "text": self.msg,
                "data": self.data,
            },
        }


class OfferStreamEvent(Event):
    offers: List[Offer]

    def to_data(self) -> dict:
        return {
            "offers": [offer.model_dump() for offer in self.offers],
        }


class OfferFilteredEvent(Event):
    offers: List[Offer]

    def to_markdown(self) -> str:
        """Convert offer to markdown format."""
        template = (
            "[{offer.name} {offer.vendor}]({offer.url})\n"
            "- ![{offer.name}]({offer.picture})\n"
            "- **Цена:** {offer.price:,.0f} ₽\n"
        )

        cards = [template.format(offer=offer) for offer in self.offers]
        return "\n\n\n".join(cards)
