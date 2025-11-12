import os
import pandas as pd
from custom_logger import LoganLogger
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# --- Vanna Imports ---
from vanna.qdrant import Qdrant_VectorStore
from vanna.google import GoogleGeminiChat
# --- End Vanna Imports ---

# Load .env file from the project root
load_dotenv() 

# --- Project Path Header ---
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
# --- END NEW PATH HEADER ---

# --- Config ---
SCHEMA_FILE_PATH = os.path.join(DATA_DIR, 'bquxjob_7414dc02_19a5d4a2dad.csv')
QDRANT_PATH = os.path.join(DATA_DIR, 'qdrant_db') 
YOUR_PROJECT_ID = ''
# --- End Config ---

# --- Define the custom Vanna class ---
class MyVanna(Qdrant_VectorStore, GoogleGeminiChat):
    def __init__(self, config=None):
        client = QdrantClient(path=QDRANT_PATH) 
        Qdrant_VectorStore.__init__(self, config={'client': client})

        GoogleGeminiChat.__init__(self, 
            config={'api_key': os.getenv('GEMINI_API_KEY'), 'model_name': os.getenv('GEMINI_MODEL')}
        )
        # --- END FIX ---

def train_vanna_from_csv(logger):
    try:
        vn_local = MyVanna()

        logger.info(f"Connecting to BigQuery project: {YOUR_PROJECT_ID}")
        vn_local.connect_to_bigquery(project_id=YOUR_PROJECT_ID)

        logger.info(f"Reading schema from local CSV: {SCHEMA_FILE_PATH}")
        df_schema = pd.read_csv(SCHEMA_FILE_PATH)
        df_schema_filtered = df_schema[['table_name', 'column_name', 'data_type']]
        
        logger.info("Converting schema DataFrame to DDL statements...")
        ddl_statements = generate_ddl_from_schema(df_schema_filtered)
        
        logger.info(f"Training Vanna locally on {len(ddl_statements)} DDL statements...")
        for ddl in ddl_statements:
            vn_local.train(ddl=ddl)
        logger.info("Training on DDL statements complete.")
        
        # --- SOPHISTICATED TRAINING ---
        logger.info("Training Vanna on sample questions (with IDs)...")
        
        # Updated to select product ID
        vn_local.train(
            question="What are the top 5 most sold products, with their IDs?",
            sql="""
                SELECT p.id, p.name, COUNT(oi.product_id) AS items_sold
                FROM `bigquery-public-data.thelook_ecommerce.order_items` AS oi
                JOIN `bigquery-public-data.thelook_ecommerce.products` AS p ON oi.product_id = p.id
                GROUP BY 1, 2
                ORDER BY 3 DESC
                LIMIT 5
            """
        )
        
        # Updated to select user ID
        vn_local.train(
            question="Who are the top 3 users by spending, with their IDs?",
            sql="""
                SELECT u.id, u.first_name, u.last_name, SUM(oi.sale_price) AS total_spent
                FROM `bigquery-public-data.thelook_ecommerce.users` AS u
                JOIN `bigquery-public-data.thelook_ecommerce.order_items` AS oi ON u.id = oi.user_id
                GROUP BY 1, 2, 3
                ORDER BY 4 DESC
                LIMIT 3
            """
        )

        # New question to train for graph exploration
        vn_local.train(
            question="Find all user IDs that used IP address '1.2.3.4'",
            sql="""
                SELECT DISTINCT user_id 
                FROM `bigquery-public-data.thelook_ecommerce.events` 
                WHERE ip_address = '1.2.3.4'
            """
        )

        # No ID needed, but still good to have
        vn_local.train(
            question="What is the total revenue?",
            sql="SELECT SUM(sale_price) AS total_revenue FROM `bigquery-public-data.thelook_ecommerce.order_items`"
        )
        # --- END SOPHISTICATED TRAINING ---

        logger.info("Training on sample questions complete.")
        logger.info("Vanna local training complete! Your model is ready.")

    except Exception as e:
        logger.error(f"Failed during Vanna training: {e}", exc_info=True)

# --- HELPER FUNCTION ---
def generate_ddl_from_schema(df_schema):
    """
    Converts a schema DataFrame (table, column, type) into a list of 
    CREATE TABLE DDL statements.
    """
    ddl_statements = []
    # This ensures Vanna knows the full table path
    dataset_id = 'bigquery-public-data.thelook_ecommerce'

    for table_name, group in df_schema.groupby('table_name'):
        columns = []
        for _, row in group.iterrows():
            columns.append(f"  {row['column_name']} {row['data_type']}")
        
        # Add the dataset_id and backticks
        ddl_string = f"CREATE TABLE `{dataset_id}.{table_name}` (\n"
        ddl_string += ",\n".join(columns)
        ddl_string += "\n);"
        ddl_statements.append(ddl_string)
    return ddl_statements
# --- END HELPER FUNCTION ---


# --- Main execution ---
if __name__ == "__main__":
    logger = LoganLogger('vanna_trainer', LOG_DIR, 'etl.log')
    
    logger.info("========================================")
    logger.info("Vanna.ai LOCAL Training Job - STARTING")
    
    if not (os.getenv('GEMINI_API_KEY') and os.getenv('GEMINI_MODEL')):
        logger.error("GEMINI_API_KEY or GEMINI_MODEL environment variable not set. Please check your .env file.")
    else:
        train_vanna_from_csv(logger)
    
    logger.info("Vanna.ai LOCAL Training Job - COMPLETE")
    logger.info("========================================")
