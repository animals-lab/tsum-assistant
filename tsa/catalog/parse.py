import json
from datetime import datetime, timedelta
from functools import cache
from pathlib import Path
from typing import Dict, Generator
from xml.etree import ElementTree as ET
from sqlalchemy import select

import qdrant_client
import requests
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import TextNode
from loguru import logger

from tsa.catalog.models import Offer
from tsa.config import settings

from tsa.config import settings
from tsa.models.catalog import Brand

# Field mappings
PARAM_FIELD_MAPPING = {
    "Цвет": "color",
    "Оттенок": "color_shade",
    "Страна дизайна": "design_country",
    "Пол": "gender",
    "Сезон": "season",
    "Материал": "material",
    "custom_categories": "category",
}


@cache
def parse_categories(file_path: Path) -> Dict[int, dict]:
    """
    Parse categories from catalog XML file and return them as a dictionary.

    Args:
        file_path: Path to the XML catalog file

    Returns:
        Dict: Dictionary containing category data with IDs as keys
    """
    categories = {}
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Find categories section
    for category in root.findall(".//category"):
        category_id = category.get("id")
        if category_id:
            categories[int(category_id)] = {
                "name": category.text,
                "url": category.get("url"),
                "parent_id": (
                    int(category.get("parentId")) if category.get("parentId") else None
                ),
            }

    # Save categories to JSON file
    output_path = settings.catalog.data_folder / "categories.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)

    print(f"Categories saved to {output_path}")
    return categories


def parse_catalog(file_path: Path) -> Generator[Offer, None, None]:
    """
    Parse catalog XML file using streaming approach.
    Yields each offer as a Pydantic model instance.

    Args:
        file_path: Path to the XML catalog file

    Yields:
        Offer: Pydantic model containing normalized offer data
    """
    context = ET.iterparse(file_path, events=("end",))
    categories = parse_categories(file_path)
    existing_brand_names = set()
    import asyncio

    for event, elem in context:
        if elem.tag == "offer":
            offer = Offer.from_xml_element(elem, categories)
            if offer.vendor not in existing_brand_names:
                existing_brand_names = asyncio.run(update_brands(offer.vendor))

            yield offer

            # Clear element to free memory
            elem.clear()

    # Clear the root element
    context.root.clear()


def download_data_file() -> Path:
    """
    Downloads file from DATA_URL and stores it in the data folder.
    Creates the data folder if it doesn't exist.
    Uses streaming to handle large files efficiently.

    Returns:
        Path: Path to the downloaded file

    Raises:
        Exception: If download fails
    """
    settings.catalog.data_folder.mkdir(exist_ok=True)

    try:
        with requests.get(settings.catalog.data_url, stream=True) as response:
            response.raise_for_status()

            with open(settings.catalog.catalog_file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        return settings.catalog.catalog_file_path

    except requests.RequestException as e:
        raise Exception(
            f"Failed to download file from {settings.catalog.data_url}: {str(e)}"
        )


def is_file_fresh(file_path: Path, max_age: timedelta) -> bool:
    """
    Check if file exists and is newer than max_age

    Args:
        file_path: Path to check
        max_age: Maximum allowed age of the file

    Returns:
        bool: True if file exists and is fresh, False otherwise
    """
    if not file_path.exists():
        return False

    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    return datetime.now() - mtime < max_age


def stream_text_nodes_from_offers(
    offers: Generator[Offer, None, None]
) -> Generator[TextNode, None, None]:
    """
    Stream conversion of Offer objects to LlamaIndex TextNode objects for indexing

    Args:
        offers: Generator of Offer objects to convert

    Yields:
        TextNode: LlamaIndex TextNode objects one at a time
    """
    for offer in offers:
        text = offer.to_text()
        metadata = offer.model_dump(exclude_none=True, exclude_unset=True)
        yield TextNode(text=text, metadata=metadata, id_=offer.uid)


async def update_brands(brand_name: str):
    async with settings.db.async_session_maker() as session:
        # Get existing brand names from database
        result = (await session.scalars(select(Brand.name))).all()
        existing_brand_names = set(result)

        if brand_name not in existing_brand_names:
            session.add(Brand(name=brand_name))
            logger.info(f"Adding brand {brand_name}")

            await session.commit()

    return existing_brand_names | {brand_name}


def load_to_qdrant(
    file_path: Path,
    collection_name: str,
    batch_size: int = 100,
) -> None:
    """
    Stream load offers into Qdrant index using batching. Only updates items that have changed.

    Args:
        file_path: Path to the catalog XML file
        collection_name: Name for the collection in Qdrant
        batch_size: Number of documents to process in each batch

    Returns:
        VectorStoreIndex: The created index
    """

    # Initialize Qdrant client
    client = settings.qdrant.client

    # Create the vector store and index
    vector_store = settings.qdrant.vector_store

    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    nodes_stream = stream_text_nodes_from_offers(parse_catalog(file_path))

    # Process nodes in batches
    batch = []
    check_batch = []
    total_processed = 0
    total_updated = 0
    total_skipped = 0

    if settings.catalog.parse_limit:
        import itertools

        logger.warning(f"Limiting to {settings.catalog.parse_limit} items")
        nodes_stream = itertools.islice(nodes_stream, settings.catalog.parse_limit)

    while True:
        node = next(
            nodes_stream, None
        )  # not while condition becase we need one extra run with None to flush batch
        if node:
            total_processed += 1
            check_batch.append(node)

        if len(check_batch) >= settings.catalog.check_size or not node:
            try:
                existing_points = client.retrieve(
                    collection_name=collection_name,
                    ids=[node.metadata["uid"] for node in check_batch],
                )
                existing_hashes = [
                    point.payload.get("hash") for point in existing_points
                ]
            except Exception as e:
                if (hasattr(e, "code") and str(e.code()) != "StatusCode.NOT_FOUND") or (
                    hasattr(e, "status_code") and e.status_code != 404
                ):
                    raise e

                logger.info("Collection not found, creating")
                existing_hashes = []

            for n in check_batch:
                if n.metadata["hash"] not in existing_hashes or not existing_hashes:
                    batch.append(n)
                else:
                    total_skipped += 1

            logger.info(
                f"Batch checked, processed {len(check_batch)} items, total skipped {total_skipped}"
            )
            check_batch = []

        if len(batch) > 0 and (len(batch) >= batch_size or not node):
            _ = VectorStoreIndex(
                batch,
                storage_context=storage_context,
                insert_mode="upsert",
            )
            total_updated += len(batch)

            logger.info(
                f"Batch finished, processed {len(batch)} items, total updated {total_updated}, total skipped {total_skipped}"
            )
            batch = []

        if not node:
            break

    create_qdrant_indexes()
    print(
        f"Processed {total_processed} documents, updated {total_updated}, skipped {total_skipped} (final batch)"
    )


def create_qdrant_indexes():
    client = settings.qdrant.client
    collection = settings.qdrant.collection

    client.create_payload_index(
        collection_name=collection,
        field_name="available",
        field_schema=qdrant_client.models.PayloadSchemaType.BOOL,
    )

    for field_name in ["price", "vendor", "color"]:
        client.create_payload_index(
            collection_name=collection,
            field_name=field_name,
            field_schema=qdrant_client.models.PayloadSchemaType.INTEGER,
        )

    for field_name in ["category", "material"]:

        client.create_payload_index(
            collection_name=collection,
            field_name=field_name,
            field_schema=qdrant_client.models.TextIndexParams(
                type="text",
                tokenizer=qdrant_client.models.TokenizerType.WORD,
                min_token_len=2,
                max_token_len=15,
                lowercase=True,
            ),
        )

    print("Indexes created")


if __name__ == "__main__":
    # Check if we need to download fresh data
    if "sample" not in settings.catalog.catalog_file_path.name:
        if not is_file_fresh(settings.catalog.catalog_file_path, timedelta(hours=1)):
            print("Downloading fresh catalog file")
            download_data_file()
        else:
            print("Using existing file - less than 1 hour old")
    else:
        print("Using sample file")

    # Parse brands first

    # # Load offers to Qdrant
    load_to_qdrant(
        file_path=settings.catalog.catalog_file_path,
        collection_name=settings.qdrant.collection,
        batch_size=settings.catalog.parse_batch,
    )

    # print("Successfully loaded offers to Qdrant index")
