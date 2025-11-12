import os
from google.adk.agents import LlmAgent
from dotenv import load_dotenv

# --- Use relative import for the package ---
from .my_tools import (
    ask_vanna_ai, 
    get_graph_connections, 
    find_shortest_path, 
    get_collaborative_recommendations,
    visualize_node_to_file
)
from .custom_logger import LoganLogger 

load_dotenv() 

# --- LOGGER SETUP ---
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
logger = LoganLogger('agent_loader', LOG_DIR, 'etl.log')
logger.info("Starting agent.py... Defining the one and only agent.")
# --- END LOGGER SETUP ---


# --- NO MORE SUB-AGENTS ---
# We are deleting SqlAgent and GraphAgent

# --- DEFINE THE ONE, ALL-POWERFUL ROOT AGENT ---
logger.info("Defining RootAgent...")
root_agent = LlmAgent(
    name="RootAgent",
    model="gemini-2.5-flash",
    description="The main coordinator for the Corporate Insights team.",
    # --- THIS IS THE NEW, SIMPLIFIED INSTRUCTION ---
    instruction=f"""
        You are a powerful and helpful AI assistant. Your job is to answer
        the user's question by following these steps:

        1.  **Analyze the Request:** Look at the user's query.
        2.  **Pick the Best Tool:** Choose the *single best tool* to answer it.
            * `ask_vanna_ai`: Use for all SQL-like questions (revenue,
                sales, counts, metrics, "top 5", "in the last 30 days").
            * `get_graph_connections`: Use *only* for simple, 1st-degree
                questions (e.g., "What did USER 123 buy?", "What is X
                connected to?").
            * `find_shortest_path`: Use *only* for "degree of separation" or
                "how are two nodes connected" questions.
            * `get_collaborative_recommendations`: Use *only* for "users who
                bought X also bought..." questions.
            * `visualize_node_to_file`: Use when the user asks to "visualize",
                "show graph", "see", or "draw" a specific node.
        3.  **Call the Tool:** Execute the tool call.
        4.  **Format the Result:** The tool will return a JSON string.
            Your final, most important job is to PARSE this JSON string
            and transform it into a beautiful, human-readable answer.

        **CRITICAL FORMATTING RULES:**
        - **DO NOT** output the raw JSON string.
        - **DO NOT** say "Here is the JSON response...".
        - Your **ONLY** output should be the human-readable formatted answer.

        ---
        **If the JSON has an "error" key:**
        Apologize and state the error.
        *Example:* "I'm sorry, I ran into an error: [error message]"

        **If the JSON has a "message" key:**
        Report the message clearly.
        *Example:* "Node USER_123 has no outgoing connections."

        **If the JSON has an "answer" key (from Vanna):**
        This is a SQL result (as a Markdown table). Present it clearly.
        *Example:*
        "Here is the data you requested:
        [The Markdown table string goes here]"

        **If the JSON has a "connections" key:**
        Format it as a bulleted list.
        *Example:*
        "Here are the direct connections for USER 8088:
        * **USES_IP:**
            * IP_ADDRESS 33.31.243.253
        * **BOUGHT:**
            * PRODUCT 13400 (Swim)"

        **If the JSON has a "path" key:**
        Format it as a clear path. The "degree_of_separation" key will also be present.
        *Example:*
        "I found a path with a degree of separation of 4:
        USER_8088 -> CENTER_02 -> PRODUCT_52342 -> USER_52"

        **If the JSON has a "recommendations" key:**
        Format it as a numbered list.
        *Example:*
        "Here are the top products users also bought:
        1.  Product 'Florida' (ID: 123) - Also bought 5 times
        2.  Product 'Fort Pierce' (ID: 456) - Also bought 3 times"
        
       **If the JSON has a "file_path" key:**
        This is a URI to a local HTML file. Format it as a clickable link.
        *Example:*
        "I have created a visualization. [Click here to view it](file_path)"
    """,
    # --- END NEW INSTRUCTION ---
    
    # --- NO MORE SUB-AGENTS ---
    sub_agents=[], 
    
    # --- ROOT AGENT NOW OWNS ALL TOOLS ---
    tools=[
        ask_vanna_ai, 
        get_graph_connections, 
        find_shortest_path, 
        get_collaborative_recommendations,
        visualize_node_to_file
    ] 
)

logger.info("Root agent defined. ADK can now load 'root_agent'.")