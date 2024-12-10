import asyncio
import os

from colorama import Fore, Style
from dotenv import load_dotenv
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.tools import BaseTool, FunctionTool
from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI

from .catalog.query import query_catalog
from utils import FunctionToolWithContext
from workflow import (
    AgentConfig,
    ConciergeAgent,
    ProgressEvent,
    ToolApprovedEvent,
    ToolRequestEvent,
)

load_dotenv()


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
        "username": None,
        "gender": None,
        "age": None,
        "preferences": {
            "styles": [],
            "colors": [],
            "budget": None,
        },
        "search_history": [],
    }


# Tools
# Fashion Assistant Tools
def get_product_search_tools() -> list[BaseTool]:
    def search_products(ctx: Context, category: str, color: str, budget: int) -> str:
        """Search for products based on category, color, and budget."""
        ctx.write_event_to_stream(
            ProgressEvent(
                msg=f"Searching for products in category '{category}', color '{color}', under budget '{budget}'."
            )
        )
        return f"Found products in category '{category}', color '{color}', under budget '{budget}'."

    def check_stock(ctx: Context, product_id: str) -> str:
        """Check if a product is in stock."""
        ctx.write_event_to_stream(
            ProgressEvent(msg=f"Checking stock for product {product_id}")
        )
        return f"Product {product_id} is in stock in sizes S, M, L"

    def get_product_reviews(ctx: Context, product_id: str, min_rating: int = 0) -> str:
        """Get reviews for a product with optional minimum rating filter."""
        ctx.write_event_to_stream(
            ProgressEvent(msg=f"Fetching reviews for product {product_id}")
        )
        return f"Product {product_id} has 4.5/5 average rating from 120 reviews"

    return [
        FunctionToolWithContext.from_defaults(fn=search_products),
        FunctionToolWithContext.from_defaults(fn=check_stock),
        FunctionToolWithContext.from_defaults(fn=get_product_reviews),
    ]


def get_trend_tools() -> list[BaseTool]:
    tavily_tool = TavilyToolSpec(api_key=os.getenv("TAVILY_API_KEY"))

    def fetch_fashion_trends(ctx: Context) -> str:
        """Fetch the latest fashion trends using web search."""
        ctx.write_event_to_stream(
            ProgressEvent(msg="Searching for latest fashion trends...")
        )
        search_results = tavily_tool.search(
            query="latest fashion trends this month, current fashion trends",
            max_results=5,
        )
        formatted_trends = "\n".join([f"- {doc.get_text()}" for doc in search_results])
        return f"Current Fashion Trends:\n{formatted_trends}"

    def get_seasonal_trends(ctx: Context, season: str) -> str:
        """Get trends for a specific season using web search."""
        ctx.write_event_to_stream(
            ProgressEvent(msg=f"Researching trends for {season}...")
        )
        search_results = tavily_tool.search(
            query=f"fashion trends for {season} season latest", max_results=3
        )
        formatted_trends = "\n".join([f"- {doc.get_text()}" for doc in search_results])
        return f"Top trends for {season}:\n{formatted_trends}"

    async def get_celebrity_styles(ctx: Context, celebrity: str) -> str:
        """Get real-time style insights from a celebrity's recent appearances."""
        chat_history = await ctx.get("chat_history", [])
        llm = await ctx.get("llm")

        # Получаем последние сообщения (пользователя и агента)
        last_messages = chat_history[-4:] if len(chat_history) >= 2 else chat_history
        dialog_context = "\n".join(
            [f"{msg.role}: {msg.content}" for msg in last_messages if msg.content]
        )

        # Используем LLM для формирования поискового запроса
        search_prompt = f"""Based on this dialog context:
            {dialog_context}

            Create a short, specific search query about {celebrity}'s fashion and style. 
            The query should be in the same language as the dialog.
            Format: Return only the search query, nothing else.
            """
        response = await llm.acomplete(search_prompt)
        search_query = response.text  # Получаем текст из ответа

        ctx.write_event_to_stream(
            ProgressEvent(
                msg=f"Dialog context:\n{dialog_context}\nSearch query: {search_query}"
            )
        )

        search_results = tavily_tool.search(query=search_query, max_results=5)
        formatted_styles = "\n".join([f"- {doc.get_text()}" for doc in search_results])
        return f"Recent dialog:\n{dialog_context}\n\n{celebrity}'s Recent Style Analysis:\n{formatted_styles}"

    return [
        FunctionToolWithContext.from_defaults(fn=fetch_fashion_trends),
        FunctionToolWithContext.from_defaults(fn=get_seasonal_trends),
        FunctionToolWithContext.from_defaults(
            fn=get_celebrity_styles, async_fn=get_celebrity_styles
        ),
    ]


def get_recommendation_tools() -> list[BaseTool]:
    def recommend_products(ctx: Context, style: str) -> str:
        """Recommend products based on a given style."""
        ctx.write_event_to_stream(
            ProgressEvent(msg=f"Recommending products for style '{style}'.")
        )
        return f"Recommendations for style '{style}': sleek loafers, tailored blazers, and silk ties."

    def get_outfit_suggestions(
        ctx: Context, occasion: str, preferred_color: str = None
    ) -> str:
        """Get outfit suggestions for specific occasions."""
        ctx.write_event_to_stream(
            ProgressEvent(msg=f"Creating outfit suggestions for {occasion}")
        )
        color_note = f" in {preferred_color}" if preferred_color else ""
        return f"For {occasion}{color_note}: Smart casual ensemble with layered accessories"

    def find_similar_items(ctx: Context, product_id: str, max_price: int = None) -> str:
        """Find similar items to a given product."""
        price_note = f" under ${max_price}" if max_price else ""
        ctx.write_event_to_stream(
            ProgressEvent(msg=f"Finding similar items to {product_id}{price_note}")
        )
        return f"Found 5 similar items to {product_id}{price_note}"

    return [
        FunctionToolWithContext.from_defaults(fn=recommend_products),
        FunctionToolWithContext.from_defaults(fn=get_outfit_suggestions),
        FunctionToolWithContext.from_defaults(fn=find_similar_items),
    ]


# Agent Configurations
def get_agent_configs() -> list[AgentConfig]:
    return [
        # AgentConfig(
        #     name="Product Search Agent",
        #     description="Searches for products, checks stock, and provides product reviews.",
        #     system_prompt="""
        #     You are a product search assistant. You can:
        #     - Search for products based on category, color, gender, and budget (min_price, max_price), material
        #     - Check if specific products are in stock
        #     - Get product reviews and ratings
        #     Important: When searching for products, always:
        #     1. Search for products first
        #     # 2. For each product found, automatically check stock availability
        #     3. Include review information when relevant
        #     Assume product IDs follow the format 'PROD_X' where X is a number (e.g., PROD_1, PROD_2).
        #     When products are found, proactively check their stock without asking the user.
        #     """,
        #     tools=get_product_search_tools(),
        #     tools_requiring_human_confirmation=["search_products", "check_stock"],
        # ),
        AgentConfig(
            name="Catalog Search Agent",
            description="Searches for products in the catalog.",
            system_prompt="""
            You are a catalog search assistant. You can:
            Search for products based on category, color, gender, and budget (min_price, max_price), material and free-form text query
            When query contains any of the parameters (category, color, gender, min_price, max_price, material), extract them from the query itself and pass as parameters.
            """,
            tools=[FunctionTool.from_defaults(async_fn=query_catalog)],
        ),
        # AgentConfig(
        #     name="Fashion Trends Agent",
        #     description="Provides information on current trends, seasonal forecasts, and celebrity styles.",
        #     system_prompt="""
        #     You are an expert on fashion trends. You can:
        #     - Provide current fashion trends
        #     - Get seasonal trend forecasts
        #     - Share celebrity style insights
            
        #     Use these tools to keep users informed about the latest in fashion.
        #     """,
        #     tools=get_trend_tools(),
        # ),
        # AgentConfig(
        #     name="Style Recommendation Agent",
        #     description="Recommends products, suggests outfits, and finds similar items.",
        #     system_prompt="""
        #     You are a style recommendation assistant. You can:
        #     - Recommend products based on style preferences
        #     - Suggest outfits for specific occasions
        #     - Find similar items to products of interest
        #     Use these tools to help users develop their personal style.
        #     """,
        #     tools=get_recommendation_tools(),
        #     tools_requiring_human_confirmation=["recommend_products"],
        # ),
    ]


# Main
async def main():
    """Main function to run the workflow."""

    llm = OpenAI(model="gpt-4o", temperature=0.4)
    memory = ChatMemoryBuffer.from_defaults(llm=llm)
    initial_state = get_initial_state()
    agent_configs = get_agent_configs()
    workflow = ConciergeAgent(timeout=None)

    # draw a diagram of the workflow
    # draw_all_possible_flows(workflow, filename="workflow.html")

    handler = workflow.run(
        user_msg="Hello!",
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
    asyncio.run(main())
