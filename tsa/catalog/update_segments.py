import csv
import asyncio
from pathlib import Path
from sqlmodel import select
from tsa.models.catalog import Brand
from tsa.config.config import settings
from loguru import logger

def read_segment_file(file_path: Path) -> list[dict]:
    segments = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for row in reader:
            segments.append({
                'brand': row[0],
                'segment': row[1],
                'price_segment': row[2]
            })
    logger.info(f"Read {len(segments)} segments from {file_path.name}")
    return segments

async def update_segments():
    data_dir = Path("data/segments")
    logger.info("Starting segments update")
    
    # Read segments data
    male_segments = read_segment_file(data_dir / "segments - buyers_мужские.csv")
    female_segments = read_segment_file(data_dir / "segments - buyers_женские.csv")
    
    created_brands = 0
    updated_brands = 0
    
    async with settings.db.async_session_maker() as session:
        # Process male segments
        logger.info("Processing male segments")
        for row in male_segments:
            result = await session.execute(select(Brand).where(Brand.name == row['brand']))
            brand = result.scalar_one_or_none()
            if not brand:
                brand = Brand(name=row['brand'])
                session.add(brand)
                created_brands += 1
            else:
                updated_brands += 1
            
            brand.segment_male = row['segment']
            brand.price_segment_male = row['price_segment']
        
        # Process female segments
        logger.info("Processing female segments")
        for row in female_segments:
            result = await session.execute(select(Brand).where(Brand.name == row['brand']))
            brand = result.scalar_one_or_none()
            if not brand:
                brand = Brand(name=row['brand'])
                session.add(brand)
                created_brands += 1
            else:
                updated_brands += 1
            
            brand.segment_female = row['segment']
            brand.price_segment_female = row['price_segment']
        
        await session.commit()
        logger.success(f"Segments update completed. Created {created_brands} new brands, updated {updated_brands} existing brands")

if __name__ == "__main__":
    asyncio.run(update_segments())
