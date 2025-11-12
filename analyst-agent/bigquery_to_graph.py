import os
import pandas as pd
import networkx as nx
import pickle 
import bigframes.pandas as bf
from custom_logger import LoganLogger  
from dotenv import load_dotenv

load_dotenv() 

# --- NEW PATH HEADER ---
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
# --- END NEW PATH HEADER ---

# --- Config ---
OUTPUT_GRAPH_FILE = os.path.join(DATA_DIR, 'graph.gpickle')
# --- End Config ---

def build_graph_with_bigframes(logger):
    """
    Combines the entire graph build process:
    1. Queries BigQuery using the bigframes API.
    2. Downloads the result to a local pandas.DataFrame.
    3. Builds the NetworkX graph in memory.
    4. Returns the graph.
    """
    logger.info("Connecting to BigQuery using bigframes...")
    try:
        bf.options.bigquery.project = 'flawless-empire-476014-j0' 
        bf.options.bigquery.location = 'US'
        
        sql = """
        SELECT
        'USER' AS source_type,
        CAST(oi.user_id AS STRING) AS source_id,
        'BOUGHT' AS relation,
        'PRODUCT' AS target_type,
        CAST(oi.product_id AS STRING) AS target_id,
        u.first_name AS source_detail,
        p.category AS target_detail
        FROM
        `bigquery-public-data.thelook_ecommerce.order_items` AS oi
        JOIN
        `bigquery-public-data.thelook_ecommerce.products` AS p
        ON
        oi.product_id = p.id
        JOIN
        `bigquery-public-data.thelook_ecommerce.users` AS u
        ON
        oi.user_id = u.id
        WHERE
        oi.user_id IS NOT NULL
        AND oi.product_id IS NOT NULL
        UNION ALL
        SELECT
        DISTINCT 'USER' AS source_type,
        CAST(user_id AS STRING) AS source_id,
        'USES_IP' AS relation,
        'IP_ADDRESS' AS target_type,
        ip_address AS target_id,
        SAFE_CAST(user_id AS STRING) AS source_detail,
        ip_address AS target_detail
        FROM
        `bigquery-public-data.thelook_ecommerce.events`
        WHERE
        user_id IS NOT NULL
        AND ip_address IS NOT NULL
        UNION ALL
        SELECT
        DISTINCT 'USER' AS source_type,
        CAST(user_id AS STRING) AS source_id,
        'USES_SESSION' AS relation,
        'SESSION' AS target_type,
        session_id AS target_id,
        SAFE_CAST(user_id AS STRING) AS source_detail,
        session_id AS target_detail
        FROM
        `bigquery-public-data.thelook_ecommerce.events`
        WHERE
        user_id IS NOT NULL
        AND session_id IS NOT NULL
        UNION ALL
        SELECT
        'USER' AS source_type,
        CAST(id AS STRING) AS source_id,
        'LOCATED_IN' AS relation,
        'CITY' AS target_type,
        city AS target_id,
        CONCAT(first_name, ' ', last_name) AS source_detail,
        state AS target_detail
        FROM
        `bigquery-public-data.thelook_ecommerce.users`
        WHERE
        id IS NOT NULL
        AND city IS NOT NULL
        UNION ALL
        SELECT
        DISTINCT 'PRODUCT' AS source_type,
        CAST(ii.product_id AS STRING) AS source_id,
        'STOCKED_AT' AS relation,
        'CENTER' AS target_type,
        CAST(ii.product_distribution_center_id AS STRING) AS target_id,
        p.name AS source_detail,
        dc.name AS target_detail
        FROM
        `bigquery-public-data.thelook_ecommerce.inventory_items` AS ii
        JOIN
        `bigquery-public-data.thelook_ecommerce.products` AS p
        ON
        ii.product_id = p.id
        JOIN
        `bigquery-public-data.thelook_ecommerce.distribution_centers` AS dc
        ON
        ii.product_distribution_center_id = dc.id
        WHERE
        ii.product_id IS NOT NULL
        AND ii.product_distribution_center_id IS NOT NULL
        UNION ALL
        SELECT
        'PRODUCT' AS source_type,
        CAST(id AS STRING) AS source_id,
        'IS_CATEGORY' AS relation,
        'CATEGORY' AS target_type,
        category AS target_id,
        name AS source_detail,
        category AS target_detail
        FROM
        `bigquery-public-data.thelook_ecommerce.products`
        WHERE
        id IS NOT NULL
        AND category IS NOT NULL
        """
        
        logger.info("Running BigQuery graph query via bigframes... (This may take a moment)")
        bigframe = bf.read_gbq(sql)
        
        logger.info("Query queued. Now downloading results to local Pandas DataFrame...")
        df = bigframe.to_pandas()
        
        logger.info(f"Data downloaded. {len(df)} rows. Converting to string.")
        df = df.astype(str).where(pd.notnull(df), None)

    except Exception as e:
        logger.error(f"Failed to query or download from BigQuery: {e}", exc_info=True)
        return None

    logger.info("Building graph from edge list...")
    G = nx.DiGraph() 
    
    for _, row in df.iterrows():
        if not all([
            row['source_type'], row['source_id'],
            row['target_type'], row['target_id'],
            row['relation']
        ]):
            continue

        source_node_id = f"{row['source_type']}_{row['source_id']}"
        target_node_id = f"{row['target_type']}_{row['target_id']}"

        G.add_node(
            source_node_id,
            type=row['source_type'],
            id=row['source_id'],
            detail=row['source_detail']
        )
        
        G.add_node(
            target_node_id,
            type=row['target_type'],
            id=row['target_id'],
            detail=row['target_detail']
        )
        
        G.add_edge(
            source_node_id,
            target_node_id,
            type=row['relation']
        )

    logger.info(f"Graph built successfully: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")
    return G

# --- Main execution ---
if __name__ == "__main__":
    logger = LoganLogger('graph_builder', LOG_DIR, 'etl.log')
    
    logger.info("========================================")
    logger.info("Graph Build Pipeline (with bigframes) - STARTING")
    
    os.makedirs(DATA_DIR, exist_ok=True)
    
    G = build_graph_with_bigframes(logger)
    
    if G:
        try:
            with open(OUTPUT_GRAPH_FILE, 'wb') as f:
                pickle.dump(G, f)
            logger.info(f"Graph saved to {OUTPUT_GRAPH_FILE}")
            logger.info("Graph Build Pipeline - COMPLETE")
        except Exception as e:
            logger.error(f"Failed to save graph: {e}", exc_info=True)
            logger.error("Graph Build Pipeline - FAILED")
    else:
        logger.error("Graph Build Pipeline - FAILED")
    
    logger.info("========================================")