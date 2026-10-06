"""
Centralized database configuration for Lakebase PostgreSQL.

This module provides configuration for connecting to Databricks Lakebase
PostgreSQL instances with OAuth authentication.

Configuration can be provided in two ways:
1. Standard PG* environment variables (automatically set when deployed to Databricks)
2. Simplified LAKEBASE_* variables for local development (auto-populated via WorkspaceClient)
"""

import logging

import os

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration for Lakebase"""
    
    def __init__(self):
        # Schema name (set via app config)
        self.SCHEMA = os.getenv("LAKEBASE_SCHEMA", "public")
        
        # Connection pool settings
        self.POOL_MIN_SIZE = int(os.getenv("POOL_MIN_SIZE", "1"))
        self.POOL_MAX_SIZE = int(os.getenv("POOL_MAX_SIZE", "5"))
        
        # Check if PG* variables are set (Databricks deployment mode)
        if os.getenv("PGHOST"):
            # Use standard PostgreSQL environment variables (set by Databricks)
            self.HOST = os.getenv("PGHOST", "")
            self.PORT = os.getenv("PGPORT", "5432")
            self.DATABASE = os.getenv("PGDATABASE", "")
            self.USER = os.getenv("PGUSER", "")
            self.SSL_MODE = os.getenv("PGSSLMODE", "require")
        else:
            # Local development mode: Use simplified variables and auto-populate
            self._init_from_lakebase_variables()
    
    def _init_from_lakebase_variables(self):
        """
        Initialize configuration from simplified LAKEBASE_* variables.
        This makes local development easier by auto-populating connection details.
        Uses WorkspaceClient to automatically get user and host from instance name.
        """
        from databricks.sdk import WorkspaceClient
        
        # Get simplified configuration
        instance_name = os.getenv("LAKEBASE_INSTANCE_NAME", "")
        database_name = os.getenv("LAKEBASE_DATABASE", "databricks_postgres")
        
        if not instance_name:
            # No configuration provided
            self.HOST = ""
            self.PORT = "5432"
            self.DATABASE = ""
            self.USER = ""
            self.SSL_MODE = "require"
            return

        # Use WorkspaceClient to get workspace details
        try:
            w = WorkspaceClient()
            
            # Get current user email
            self.USER = w.current_user.me().user_name
            
            # Get database instance host using the proper API
            self.HOST = w.database.get_database_instance(name=instance_name).read_write_dns
            
            self.DATABASE = database_name
            self.PORT = "5432"
            self.SSL_MODE = "require"
            
        except Exception as e:
            # If WorkspaceClient fails, set empty values
            logger.warning(f"Could not auto-populate database config: {e}")
            self.HOST = ""
            self.PORT = "5432"
            self.DATABASE = database_name
            self.USER = ""
            self.SSL_MODE = "require"
    
    def get_full_table_name(self, table_name: str) -> str:
        """
        Get the full table name in format schema.table
        
        Args:
            table_name: The table name without schema
            
        Returns:
            str: Full table name with schema
        """
        if self.SCHEMA and self.SCHEMA != "public":
            return f"{self.SCHEMA}.{table_name}"
        return table_name
    
    def get_schema_name(self) -> str:
        """Get the current schema name"""
        return self.SCHEMA


# Singleton instance
db_config = DatabaseConfig()

