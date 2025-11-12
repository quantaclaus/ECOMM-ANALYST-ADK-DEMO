Corporate Insights Agent: Vanna (SQL) + NetworkX (Graph)

This project implements a sophisticated AI agent using the google-adk framework. It provides a single interface to answer complex business questions by intelligently routing queries to one of two powerful backends:

Vanna.ai (SQL Analytics): Leverages a local Qdrant vector store and Google's Gemini model to translate natural language questions into BigQuery SQL. It's ideal for quantitative analysis, metrics, and data retrieval (e.g., "What was our total revenue last month?").

NetworkX (Graph Analytics): Uses a pre-built graph database (graph.gpickle) to explore complex, non-obvious relationships between corporate entities (users, products, IP addresses, etc.). It's built for qualitative analysis, fraud detection, and recommendations (e.g., "How is User 123 connected to User 456?").

The RootAgent is designed to analyze a user's prompt, select the single best tool for the job, and then format the JSON output from that tool into a clean, human-readable answer.

🚀 Core Features

Intelligent Tool Routing: A single RootAgent analyzes user queries and decides whether to use a SQL or Graph tool.

Natural Language to SQL: Ask quantitative questions in plain English. The agent generates, executes, and returns BigQuery SQL results (powered by Vanna).

1st-Degree Graph Traversal: Ask for the direct connections of any node (e.g., "What did USER 123 buy?").

Degree-of-Separation Analysis: Find the shortest path between any two nodes in the graph (e.g., "Show me the connection between USER_123 and IP_4.5.6.7").

Collaborative Filtering: Get "users who bought this also bought..." recommendations based on shared purchasing history.

Interactive Graph Visualization: Ask the agent to "visualize" or "show" a node, and it will generate an interactive Plotly HTML file visualizing that node's 1-degree neighborhood.

🏗️ Architecture & Data Flow

The project is split into two phases: a one-time "ETL/Training" phase and an ongoing "Runtime" phase.

1. Offline ETL & Training (One-Time Setup)

Before the agent can run, its knowledge bases must be built:

Graph Build (bigquery_to_graph.py):

Connects to BigQuery using bigframes.

Executes a large SQL query to fetch all entity relationships (User-Product, User-IP, Product-Category, etc.).

Builds a networkx.DiGraph in memory.

Saves the final graph to data/graph.gpickle.

Vanna Training (vanna_trainer.py):

Connects to BigQuery.

Reads a local schema file (data/bquxjob_...csv).

Generates DDL (Data Definition Language) statements for all tables.

Trains a local MyVanna instance on these DDLs, storing the embeddings in a local Qdrant DB (data/qdrant_db).

Performs "sophisticated training" by adding specific question-SQL pairs for common, complex queries.

2. Online Agent Runtime (Live Queries)

A user runs the agent (e.g., using the adk chat CLI).

The user submits a prompt (e.g., "What are the top 5 most sold products?").

The RootAgent (agent.py) receives the prompt.

Its instructions guide it to select the single best tool from my_tools.py. In this case, it chooses ask_vanna_ai.

ask_vanna_ai (from my_tools.py) queries the local Qdrant DB, finds the most relevant training data, generates SQL, executes it on BigQuery, and gets a result.

The tool returns a JSON string to the agent: {"status": "success", "answer": "[Markdown table...]", "query": "SELECT ..."}.

The RootAgent's prompt instructions then force it to parse this JSON and format it as a human-readable response, not as raw JSON.

🛠️ Setup & Installation

Clone Repository:

git clone [your-repo-url]
cd [your-repo-name]


Create Virtual Environment & Install Dependencies:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt


Google Cloud Authentication:
This project queries BigQuery. Ensure your local environment is authenticated:

gcloud auth application-default login


Note: The project ID flawless-empire-476014-j0 is hardcoded in vanna_trainer.py, bigquery_to_graph.py, and my_tools.py. You may need to update this to your own GCP project ID.

Create .env File:
Create a .env file in the project root:

GEMINI_API_KEY="your_google_gemini_api_key_here"
GEMINI_MODEL="gemini-1.5-flash-latest" 


Add Schema Data:
The Vanna trainer requires a CSV dump of your database schema.

Place your schema file at: data/bquxjob_7414dc02_19a5d4a2dad.csv.

If your file has a different name, update the SCHEMA_FILE_PATH variable in vanna_trainer.py.

🚀 How to Run

You must run the one-time ETL scripts before you can run the agent.

Step 1: Run ETL & Training (One-Time)

These scripts will query BigQuery and create your local data artifacts.

Build the Graph:

python src/bigquery_to_graph.py


Output: Creates data/graph.gpickle. You will see log messages in logs/etl.log.

Train the Vanna Model:

python src/vanna_trainer.py


Output: Creates/updates the data/qdrant_db directory.

Step 2: Run the Agent

Once the artifacts in data/ exist, you can run the RootAgent using the google-adk CLI.

To chat in your terminal:

adk chat -a src/agent.py:root_agent


To serve the agent via an API (and use the ADK testbed):

adk serve -a src/agent.py:root_agent


You can then access the ADK testbed at http://127.0.0.1:8000/.

Example Questions

Vanna (SQL): "What is our total revenue?"

Vanna (SQL): "Show me the top 3 users by total spending, with their IDs."

Vanna (SQL): "Find all user IDs that used IP address '1.2.3.4'"

Graph (Connections): "What is USER 8088 connected to?"

Graph (Pathfinding): "How is USER 8088 connected to USER 100?"

Graph (Recommendation): "Users who bought product 24747 also bought what?"

Graph (Visualization): "Can you show me a graph of USER 8088?"

📂 Project Structure

.
├── data/
│   ├── bquxjob_7414dc02_19a5d4a2dad.csv  # (REQUIRED) Input schema for Vanna
│   ├── graph.gpickle                     # (Generated) The NetworkX graph
│   └── qdrant_db/                        # (Generated) The Vanna vectorstore
├── logs/
│   └── etl.log                           # (Generated) Log file for all modules
├── src/
│   ├── __init__.py
│   ├── agent.py                          # Defines the main RootAgent
│   ├── bigquery_to_graph.py              # ETL script to build the graph
│   ├── custom_logger.py                  # Utility for shared logging
│   ├── my_tools.py                       # Defines the 5 tools for the agent
│   └── vanna_trainer.py                  # ETL script to train Vanna
├── .env                                  # (REQUIRED) Stores API keys
├── requirements.txt
└── README.md
