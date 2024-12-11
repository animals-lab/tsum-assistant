from enum import Enum
from typing import List, Optional

from llama_index.core.workflow import Event
from app.catalog.models import Offer


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
            "TransferToAgent": "Координатор",
            "query_catalog_short": "Поиск в каталоге",
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