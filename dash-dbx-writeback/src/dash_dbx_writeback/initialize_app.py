"""
Application Initialization Module

Automatically initializes database tables with sample data on app startup
if they are empty. This ensures the app has data to display on first run.
"""

import logging

import pandas as pd
from typing import Dict, Any

from .config import db_config

from .database_operations import (
    check_table_exists,
    query_df,
    bulk_insert,
)
from .sample_data import INITIAL_DATA

logger = logging.getLogger(__name__)


def initialize_tables_on_startup():
    """
    Initialize database tables with sample data if they are empty.
    Called automatically when the app starts.
    """
    logger.info("CHECKING DATABASE INITIALIZATION")
    
    # Define tables to initialize
    tables_to_check = {
        'layout_data': INITIAL_DATA,
    }
    
    for table_name, sample_data in tables_to_check.items():
        try:
            full_table_name = db_config.get_full_table_name(table_name)
            logger.info(f"Checking table: {full_table_name}")
            
            # Check if table exists
            if not check_table_exists(full_table_name):
                logger.warning(f"Table '{full_table_name}' does not exist")
                logger.info("Creating table and inserting sample data...")
                
                # Create DataFrame from sample data
                df = pd.DataFrame(sample_data)
                
                # Create table and insert data
                result = bulk_insert(full_table_name, df, overwrite=True)
                logger.info(f"Created table '{full_table_name}' with {result} rows")
                
            else:
                # Table exists, check if it's empty
                logger.info(f"Table '{full_table_name}' exists")
                
                # Count rows
                count_query = f"SELECT COUNT(*) as count FROM {full_table_name}"
                count_df = query_df(count_query)
                
                if not count_df.empty:
                    row_count = count_df.iloc[0]['count']
                    logger.info(f"Current row count: {row_count}")
                    
                    if row_count == 0:
                        logger.warning("Table is empty, inserting sample data...")
                        
                        # Insert sample data
                        df = pd.DataFrame(sample_data)
                        result = bulk_insert(full_table_name, df, overwrite=False)
                        logger.info(f"Inserted {result} rows into '{full_table_name}'")
                    else:
                        logger.info("Table has data, skipping initialization")
                        
        except Exception as e:
            logger.exception(f"Error initializing table '{table_name}': {e}")
            # Continue with other tables even if one fails
            continue
    
    logger.info("DATABASE INITIALIZATION COMPLETE")


def get_table_stats() -> Dict[str, Any]:
    """
    Get statistics about initialized tables.
    
    Returns:
        dict: Table statistics including row counts
    """
    stats = {}
    
    tables = ['layout_data']
    
    for table_name in tables:
        try:
            full_table_name = db_config.get_full_table_name(table_name)
            
            if check_table_exists(full_table_name):
                count_query = f"SELECT COUNT(*) as count FROM {full_table_name}"
                count_df = query_df(count_query)
                
                if not count_df.empty:
                    stats[table_name] = {
                        'exists': True,
                        'row_count': int(count_df.iloc[0]['count'])
                    }
                else:
                    stats[table_name] = {'exists': True, 'row_count': 0}
            else:
                stats[table_name] = {'exists': False, 'row_count': 0}
                
        except Exception as e:
            stats[table_name] = {'exists': False, 'error': str(e)}
    
    return stats


if __name__ == "__main__":
    # Allow running this module directly for manual initialization
    initialize_tables_on_startup()
    for table, info in get_table_stats().items():
        if info.get('exists'):
            logger.info(f"Table {table}: {info.get('row_count', 0)} rows")
        else:
            logger.warning(f"Table {table}: not found {info.get('error', '')}".strip())

