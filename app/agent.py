import asyncio
import os

from colorama import Fore, Style
from dotenv import load_dotenv
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import BaseTool, FunctionTool
from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI
from llama_index.llms.perplexity import Perplexity
from llama_index.core.llms import ChatMessage

from .catalog.query import query_catalog_short
from .utils import FunctionToolWithContext
from .workflow import (
    AgentConfig,
    ConciergeAgent,
    ProgressEvent,
    ToolApprovedEvent,
    ToolRequestEvent,
)

load_dotenv()

import logging
logger = logging.getLogger(__name__)


# Add this color mapping near the top of the file, after imports
AGENT_COLORS = {
    "Product Search Agent": Fore.MAGENTA,
    "Fashion Trends Agent": Fore.LIGHTRED_EX,
    "Style Recommendation Agent": Fore.YELLOW,
    "Orchestrator": Fore.LIGHTBLUE_EX,
    "Unknown Agent": Fore.WHITE,
}


# Initial user state
def get_initial_state() -> dict:
    return {
        "username": "Кабаныч",
        "gender": "male",
        "age": 25,
        "preferences": {
            "styles": ["streetwear", "casual"],
            "colors": ["black", "white", "gray"],
            "budget": 1000000,
        },
        "search_history": ["stone island", "supreme", "off-white", "balenciaga"],
    }


# Tools
# Add this near the top of the file with other global variables
perplexity_llm = Perplexity(
    api_key=os.getenv("PERPLEXITY_API_KEY"),
    model="llama-3.1-sonar-small-128k-online",
    temperature=0.5
)

# Replace the get_trend_tools function
def get_trend_tools() -> list[BaseTool]:
    async def fetch_fashion_trends(ctx: Context) -> str:
        """Useful tool for fetching the latest information from the internet. Use it for any user query about fashion."""
        try:
            chat_history = await ctx.get("chat_history", [])
            
            # Get the latest user message
            latest_user_msg = None
            for msg in reversed(chat_history):
                if msg.role == "user":
                    latest_user_msg = msg.content
                    break
            
            if not latest_user_msg:
                latest_user_msg = "Tell me about fashion"  # fallback query
                
            logger.info(f"Using latest user message: {latest_user_msg}")
            
            ctx.write_event_to_stream(
                ProgressEvent(msg=f"Querying Perplexity with: {latest_user_msg}")
            )
            
            messages_dict = [
                {
                    "role": "system", 
                    "content": "You are a fashion expert. Provide relevant and detailed responses about fashion, trends, and style."
                },
                {
                    "role": "user", 
                    "content": latest_user_msg
                },
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
""" + "\n".join([f"[{i+1}] {citation}" for i, citation in enumerate(full_response['citations'])])
            
            return formatted_response
            
        except Exception as e:
            error_msg = f"Error testing Perplexity: {str(e)}"
            logger.error(error_msg)
            return error_msg

    return [
        FunctionToolWithContext.from_defaults(
            fn=fetch_fashion_trends,
            async_fn=fetch_fashion_trends
        )
    ]




# Agent Configurations
def get_agent_configs() -> list[AgentConfig]:
    return [
        # CATALOG SEARCH AGENT
        AgentConfig(
            name="Catalog Search Agent",
            description="""Use this agent when user wants to:
            - Find or search for specific products
            - Look for items with specific colors, brands, or characteristics
            - Search the catalog
            - Find clothes, shoes, or accessories
            
            Keywords that indicate catalog search:
            - найти, поиск, ищу, покажи
            - любые конкретные товары (кеды, платье, куртка, etc.)
            - указание цветов или брендов
            """,
            system_prompt="""
            You are a catalog search assistant. You can search for products using these parameters:
            - query_text (string): Use for free-form text search (e.g., "кеды", "элегантное платье")
            - color (list[str]): List of colors (e.g., ["Белый", "Черный"])
            - gender (str): Gender ("Мужской", "Женский", or "Унисекс")
            - vendor (list[str], optional): List of brand names
            - min_price (float, optional): Minimum price
            - max_price (float, optional): Maximum price
            - material (list[str], optional): List of materials

            IMPORTANT RULES:
            1. ALWAYS use query_text for the main search term
            2. NEVER use the 'category' parameter - include category terms in query_text instead
            3. For colors, use exact matches like "Белый" (not "белый")
            4. For gender, use exact match "Мужской" (not "мужской")

            Example correct usage:
            ```python
            {
                "query_text": "кеды",
                "color": ["Белый"],
                "gender": "Мужской"
            }
            ```
            """,
            tools=[FunctionTool.from_defaults(async_fn=query_catalog_short)],
        ),

        # STYLIST AGENT
        AgentConfig(
            name="Stylist Agent",
            description="""Use this agent ONLY for fashion advice and trend questions. Examples:
            - Что сейчас в моде?
            - Какие тренды в этом сезоне?
            - Как стильно одеваться?
            - Какие цвета популярны?
            - Как сочетать вещи?
            
            DO NOT use for product searches or catalog queries.""",
            system_prompt="""
            You are a fashion expert and personal stylist. Your role is to provide fashion advice and trend information.
            
            CRITICAL RULES ABOUT TRANSFERS:
            1. IMMEDIATELY request transfer to Catalog Search Agent if user:
               - Mentions ANY specific items (куртка, платье, кеды, etc.)
               - Uses ANY search-related words (найти, покажи, ищу, etc.)
               - Asks about prices or availability
               - Mentions colors of specific items
               - Uses words like "купить", "заказать", "приобрести"
               DO NOT try to answer these queries yourself - TRANSFER IMMEDIATELY
            
            RULES FOR FASHION ADVICE:
            1. For pure fashion advice queries:
               - ALWAYS use the fetch_fashion_trends tool
               - Return the EXACT formatted response from the tool
               - DO NOT modify or summarize the response
            
            Example conversation:
            User: "Что сейчас в моде?"
            You: *use fetch_fashion_trends and return its exact response*
            
            User: "Как сочетать цвета?"
            You: *use fetch_fashion_trends and return its exact response*
            
            User: "Хочу купить куртку" or "Покажи белые кеды" or "Ищу платье"
            You: *IMMEDIATELY request transfer to Catalog Search Agent*
            
            REMEMBER: If there's ANY hint of product search, TRANSFER to Catalog Search Agent immediately!
            """,
            tools=get_trend_tools(),
        ),
    ]





# Main
async def main():
    """Main function to run the workflow."""

    llm = OpenAI(model="gpt-4o-mini", temperature=0.4)
    memory = ChatMemoryBuffer.from_defaults(llm=llm)
    initial_state = get_initial_state()
    agent_configs = get_agent_configs()
    workflow = ConciergeAgent(timeout=None)

    # draw a diagram of the workflow
    # draw_all_possible_flows(workflow, filename="workflow.html")

    handler = workflow.run(
        user_msg="Привет!",
        agent_configs=agent_configs,
        llm=llm,
        chat_history=[],
        initial_state=initial_state,
    )

    while True:
        async for event in handler.stream_events():
            if isinstance(event, ToolRequestEvent):
                print(
                    Fore.GREEN
                    + "SYSTEM >> I need approval for the following tool call:"
                    + Style.RESET_ALL
                )
                print(event.tool_name)
                print(event.tool_kwargs)
                print()

                approved = input("Do you approve? (y/n): ")
                if "y" in approved.lower():
                    handler.ctx.send_event(
                        ToolApprovedEvent(
                            tool_id=event.tool_id,
                            tool_name=event.tool_name,
                            tool_kwargs=event.tool_kwargs,
                            approved=True,
                        )
                    )
                else:
                    reason = input("Why not? (reason): ")
                    handler.ctx.send_event(
                        ToolApprovedEvent(
                            tool_name=event.tool_name,
                            tool_id=event.tool_id,
                            tool_kwargs=event.tool_kwargs,
                            approved=False,
                            response=reason,
                        )
                    )
            elif isinstance(event, ProgressEvent):
                print(Fore.GREEN + f"SYSTEM >> {event.msg}" + Style.RESET_ALL)

        result = await handler
        agent_name = result.get("agent_name", "Unknown Agent")
        agent_color = AGENT_COLORS.get(
            agent_name, Fore.WHITE
        )  # Default to white if agent not found
        print(f"{agent_color}[{agent_name}] >> {result['response']}{Style.RESET_ALL}")

        # update the memory with only the new chat history
        for i, msg in enumerate(result["chat_history"]):
            if i >= len(memory.get()):
                memory.put(msg)

        user_msg = input("USER >> ")
        if user_msg.strip().lower() in ["exit", "quit", "bye"]:
            break

        # pass in the existing context and continue the conversation
        handler = workflow.run(
            ctx=handler.ctx,
            user_msg=user_msg,
            agent_configs=agent_configs,
            llm=llm,
            chat_history=memory.get(),
            initial_state=initial_state,
        )


if __name__ == "__main__":
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # This will output to console
        ]
    )
    logger = logging.getLogger(__name__)
    
    asyncio.run(main())
