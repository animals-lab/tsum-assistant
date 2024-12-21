import logging

from llama_index.core.llms import ChatMessage
from llama_index.llms.perplexity import Perplexity

logger = logging.getLogger(__name__)
import os

perplexity_llm = Perplexity(
    api_key=os.getenv("PERPLEXITY_API_KEY"),
    model="llama-3.1-sonar-small-128k-online",
    temperature=0.5,
)


async def fetch_fashion_trends(query: str) -> str:
    """Useful tool for fetching the latest information from the internet. Use it for any user query about fashion."""
    try:
        latest_user_msg = query

        logger.info(f"Using latest user message: {latest_user_msg}")

        # ctx.write_event_to_stream(
        #     ProgressEvent(msg=f"Querying Perplexity with: {latest_user_msg}")
        # )

        messages_dict = [
            {
                "role": "system",
                "content": "You are a fashion expert. Provide relevant and detailed responses about fashion, trends, and style.",
            },
            {"role": "user", "content": latest_user_msg},
        ]

        messages = [ChatMessage(**msg) for msg in messages_dict]

        logger.info("Sending request to Perplexity...")
        response = perplexity_llm.chat(messages)
        logger.info(f"Received response: {response}")

        full_response = {
            "content": response.message.content,
            "citations": response.raw.get("citations", []),
        }

        logger.info(f"Formatted response: {full_response}")

        formatted_response = f"""
Response from Perplexity:
------------------------
Query: {latest_user_msg}

{full_response['content']}

Citations:
---------
""" + "\n".join(
            [
                f"[{i+1}] {citation}"
                for i, citation in enumerate(full_response["citations"])
            ]
        )

        return formatted_response

    except Exception as e:
        error_msg = f"Error testing Perplexity: {str(e)}"
        logger.error(error_msg)
        return error_msg
