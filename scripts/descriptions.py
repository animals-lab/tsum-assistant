import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
import argparse
import requests
from loguru import logger
import tiktoken

def get_all_categories(url: str) -> Dict[str, int]:
    """
    Fetch all available categories and their counts from Qdrant.
    
    Args:
        url: Base Qdrant URL
        
    Returns:
        Dictionary mapping category names to their counts
    """
    logger.info("Fetching all available categories...")
    
    payload = {
        "limit": 1000,  # Large enough to get a good sample
        "with_payload": ["categories"],
    }
    
    try:
        response = requests.post(f"{url}/points/scroll", json=payload)
        response.raise_for_status()
        
        category_counts = {}
        points = response.json().get('result', {}).get('points', [])
        
        for point in points:
            categories = point.get('payload', {}).get('categories', [])
            for category in categories:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # Sort by count descending
        sorted_categories = dict(sorted(
            category_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        logger.info(f"Found {len(sorted_categories)} unique categories")
        return sorted_categories
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return {}

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in a text using OpenAI's tokenizer.
    
    Args:
        text: Text to count tokens for
        model: Model name to use for tokenization
        
    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.error(f"Error counting tokens: {str(e)}")
        # Fallback to approximate count (avg 4 chars per token)
        return len(text) // 4

def scroll_points(categories: Optional[List[str]] = None, limit: int = 10, raw: bool = False, max_tokens: Optional[int] = None):
    """
    Make a request to Qdrant endpoint to scroll through points and save descriptions to a file.
    
    Args:
        categories: Optional list of categories to filter by. If None, all descriptions are fetched.
        limit: Maximum number of items to fetch. Defaults to 10.
        raw: If True, output only raw descriptions list without metadata.
        max_tokens: Maximum number of tokens to collect (for LLM context window)
    """
    url = "http://10.70.4.201:6333/collections/tsum_catalog_openai_small/points/scroll"
    output_dir = Path("data/descriptions")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a filename that includes category info if specified
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    category_suffix = f"_{'-'.join(categories)}" if categories else ""
    token_suffix = f"_{max_tokens}tok" if max_tokens else ""
    output_file = output_dir / f"descriptions{category_suffix}{token_suffix}.{'txt' if raw else 'json'}"
    
    if not raw:
        all_descriptions = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "source": url,
                "total_points": 0,
                "collection": "tsum_catalog_openai_small",
                "categories": categories,
                "limit": limit,
                "max_tokens": max_tokens,
                "total_tokens": 0,
                "stats": {
                    "empty_descriptions": 0,
                    "avg_description_length": 0,
                    "min_description_length": float('inf'),
                    "max_description_length": 0,
                    "length_distribution": {
                        "short": 0,    # < 50 chars
                        "medium": 0,   # 50-200 chars
                        "long": 0      # > 200 chars
                    }
                }
            },
            "descriptions": []
        }
    else:
        raw_descriptions = []
    
    offset = None
    total_points = 0
    total_tokens = 0
    separator_tokens = count_tokens("\n---\n")  # Count tokens in separator
    
    try:
        while (total_points < limit) and (not max_tokens or total_tokens < max_tokens):
            remaining_items = limit - total_points
            batch_size = min(100, remaining_items)
            
            payload = {
                "limit": batch_size,
                "with_payload": ["description", "categories", "url", "tsum_sku", "vendor_sku", "name", "vendor"],
                "offset": offset
            }
            
            if categories:
                payload["filter"] = {
                    "must": [{
                        "key": "categories",
                        "match": {
                            "any": categories
                        }
                    }]
                }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            points = data.get('result', {}).get('points', [])
            
            if not points:
                break
                
            for point in points:
                payload = point.get('payload', {})
                description = payload.get('description', '')
                
                if not description:
                    continue
                    
                # Count tokens in this description
                desc_tokens = count_tokens(description)
                
                # Check if adding this description would exceed token limit
                if max_tokens and (total_tokens + desc_tokens + separator_tokens > max_tokens):
                    logger.info(f"Reached token limit of {max_tokens} tokens")
                    break
                
                total_tokens += desc_tokens + separator_tokens
                total_points += 1
                
                if raw:
                    raw_descriptions.append(description)
                else:
                    length = len(description)
                    description_entry = {
                        "id": point.get('id'),
                        "tsum_sku": payload.get('tsum_sku'),
                        "vendor_sku": payload.get('vendor_sku'),
                        "name": payload.get('name'),
                        "vendor": payload.get('vendor'),
                        "url": payload.get('url'),
                        "description": description,
                        "length": length,
                        "tokens": desc_tokens,
                        "has_description": True,
                        "categories": payload.get('categories', [])
                    }
                    all_descriptions["descriptions"].append(description_entry)
                    
                    # Update length statistics
                    all_descriptions["metadata"]["stats"]["min_description_length"] = min(
                        all_descriptions["metadata"]["stats"]["min_description_length"], 
                        length
                    )
                    all_descriptions["metadata"]["stats"]["max_description_length"] = max(
                        all_descriptions["metadata"]["stats"]["max_description_length"], 
                        length
                    )
                    
                    if length < 50:
                        all_descriptions["metadata"]["stats"]["length_distribution"]["short"] += 1
                    elif length < 200:
                        all_descriptions["metadata"]["stats"]["length_distribution"]["medium"] += 1
                    else:
                        all_descriptions["metadata"]["stats"]["length_distribution"]["long"] += 1
            
            if max_tokens and (total_tokens >= max_tokens):
                break
                
            offset = data.get('result', {}).get('next_page_offset')
            if not offset:
                break
                
        if raw:
            with open(output_file, 'w', encoding='utf-8') as f:
                for desc in raw_descriptions:
                    f.write(f"{desc}\n---\n")
            logger.info(f"Successfully saved {len(raw_descriptions)} descriptions ({total_tokens} tokens) to {output_file}")
        else:
            # Update final metadata
            stats = all_descriptions["metadata"]["stats"]
            stats["total_points"] = total_points
            stats["empty_descriptions"] = 0  # We skip empty descriptions now
            
            if total_points > 0:
                stats["avg_description_length"] = sum(
                    d["length"] for d in all_descriptions["descriptions"]
                ) / total_points
            
            if stats["min_description_length"] == float('inf'):
                stats["min_description_length"] = 0
                
            all_descriptions["metadata"]["total_tokens"] = total_tokens
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_descriptions, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Successfully saved {total_points} descriptions ({total_tokens} tokens) to {output_file}")
            logger.info(f"Metadata: {json.dumps(all_descriptions['metadata'], indent=2)}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making request to Qdrant: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

def main():
    """
    Main function to handle script execution with different options.
    """
    parser = argparse.ArgumentParser(description='Fetch product descriptions from Qdrant')
    parser.add_argument('--limit', type=int, default=10, help='Number of items to fetch (ignored if --context is used)')
    parser.add_argument('--category', help='Specific category to fetch')
    parser.add_argument('--list-categories', action='store_true', help='List all available categories and exit')
    parser.add_argument('--raw', action='store_true', help='Output only raw descriptions list')
    parser.add_argument('--context', type=str, 
                       help='Context length in thousands (e.g., 128k, 8k, 16k). Will use 80%% of this for descriptions.')
    args = parser.parse_args()
    
    # Parse context length if provided
    max_tokens = None
    if args.context:
        try:
            # Extract number from string like "128k"
            k_value = int(args.context.lower().rstrip('k'))
            # Convert to tokens and take 80% to leave room for prompt and response
            max_tokens = int(k_value * 1000 * 0.8)
            logger.info(f"Using {max_tokens} tokens out of {k_value}k context length")
            # When using token limit, set item limit very high
            args.limit = 1000000
        except ValueError:
            logger.error("Invalid context length format. Use format like '128k', '8k', '16k'")
            return
    
    base_url = "http://10.70.4.201:6333/collections/tsum_catalog_openai_small"
    
    if args.list_categories:
        categories = get_all_categories(base_url)
        print("\nAvailable categories (with item counts):")
        for category, count in categories.items():
            print(f"{category}: {count}")
        return
    
    if args.category:
        categories = get_all_categories(base_url)
        if args.category not in categories:
            logger.error(f"Invalid category: {args.category}")
            return
        logger.info(f"Fetching items for category: {args.category}")
        scroll_points(categories=[args.category], limit=args.limit, raw=args.raw, max_tokens=max_tokens)
    else:
        logger.info("Fetching items without category filter...")
        scroll_points(limit=args.limit, raw=args.raw, max_tokens=max_tokens)

if __name__ == "__main__":
    main() 