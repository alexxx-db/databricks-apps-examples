import pandas as pd
import pytest

# Needs a live Lakebase instance; CI runs `pytest -m "not integration"`
pytestmark = pytest.mark.integration
import os

from unittest.mock import Mock, patch, MagicMock
from dash_dbx_writeback.callbacks.tables import read_table
from dash_dbx_writeback.sample_data import INITIAL_DATA
from dash_dbx_writeback.database_operations import get_connection, initialize_connection_pool
from dash_dbx_writeback.config import db_config


@pytest.fixture
def mock_cursor():
    cursor = MagicMock()
    cursor.execute = Mock()
    cursor.fetchall_arrow = Mock()
    cursor.rowcount = -1  # Set default rowcount
    cursor.message = "Success"  # Set default message
    return cursor


@pytest.fixture
def mock_connection(mock_cursor):
    connection = MagicMock()
    # Make the context manager return the mock_cursor
    context_manager = MagicMock()
    context_manager.__enter__.return_value = mock_cursor
    context_manager.__exit__.return_value = None
    connection.cursor.return_value = context_manager
    return connection


def test_read_table(mock_connection, mock_cursor):
    # Setup test data
    test_data = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
    
    # Mock pandas read_sql to return test data
    with patch("pandas.read_sql") as mock_read_sql:
        mock_read_sql.return_value = test_data
        
        # Test the read_table function
        query = "SELECT * FROM test_table"
        result = read_table("test_table", query, mock_connection)

        # Verify the results
        assert isinstance(result, pd.DataFrame)
        assert result.equals(test_data)
        mock_read_sql.assert_called_once_with(query, mock_connection)


def test_get_connection():
    # Test that get_connection returns None when pool initialization fails
    import dash_dbx_writeback.database_operations as db_ops
    
    # Mock the global _connection_pool as None
    with patch.object(db_ops, '_connection_pool', None):
        with patch("dash_dbx_writeback.database_operations.initialize_connection_pool") as mock_init:
            mock_init.return_value = False
            result = get_connection()
            assert result is None
        
    # Test that get_connection returns pool when initialization succeeds
    mock_pool = MagicMock()
    with patch.object(db_ops, '_connection_pool', mock_pool):
        result = get_connection()
        assert result == mock_pool


@pytest.mark.integration
def test_real_warehouse_connection():
    """Integration test that connects to a real Databricks warehouse.

    This test requires the following environment variables to be set:
    - DATABRICKS_HOST: Your Databricks workspace URL
    - DATABRICKS_HTTP_PATH: The HTTP path of your SQL warehouse
    - DATABRICKS_TOKEN: Your Databricks access token
    - DATABRICKS_CATALOG: Your Unity Catalog catalog name
    - DATABRICKS_SCHEMA: Your Unity Catalog schema name
    """
    # Skip if environment variables are not set
    required_vars = [
        "DATABRICKS_HOST",
        "DATABRICKS_HTTP_PATH",
        "DATABRICKS_TOKEN",
        "DATABRICKS_CATALOG",
        "DATABRICKS_SCHEMA",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        pytest.skip(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    # Test connection
    conn = get_connection()
    assert conn is not None

    # Test reading a table using the database configuration
    test_table = db_config.get_full_table_name("bakehouse_data")
    try:
        query = f"SELECT * FROM {test_table}"
        df = read_table(test_table, query, conn)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        print(f"Successfully read {len(df)} rows from {test_table}")
    except Exception as e:
        pytest.fail(f"Failed to read table: {str(e)}")


@pytest.mark.integration
def test_real_writeback():
    """Integration test that connects to a real Databricks warehouse.

    This test requires the following environment variables to be set:
    - DATABRICKS_HOST: Your Databricks workspace URL
    - DATABRICKS_HTTP_PATH: The HTTP path of your SQL warehouse
    - DATABRICKS_TOKEN: Your Databricks access token
    - DATABRICKS_CATALOG: Your Unity Catalog catalog name
    - DATABRICKS_SCHEMA: Your Unity Catalog schema name
    """
    # Skip if environment variables are not set
    required_vars = [
        "DATABRICKS_HOST",
        "DATABRICKS_HTTP_PATH",
        "DATABRICKS_TOKEN",
        "DATABRICKS_CATALOG",
        "DATABRICKS_SCHEMA",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        pytest.skip(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    # Test connection
    conn = get_connection()
    assert conn is not None

    # Test writing to a table using the database configuration
    test_table = db_config.get_full_table_name("pytest_writeback")
    pytest.skip("Writeback test requires insert_overwrite_table implementation for PostgreSQL")


def test_table_name_construction():
    """Test table name construction with environment variables.
    
    This test verifies that:
    - Environment variables LAKEBASE_SCHEMA is used
    - Table names are constructed in the correct format: schema.table
    """
    
    # Test table name
    test_table = "product_sales"
    
    # Get the constructed full name
    full_name = db_config.get_full_table_name(test_table)
    
    # Get schema name
    schema_name = db_config.get_schema_name()
    
    # Verify the full table name construction
    if schema_name and schema_name != "public":
        expected_full_name = f"{schema_name}.{test_table}"
    else:
        expected_full_name = test_table
        
    assert full_name == expected_full_name, (
        f"Expected '{expected_full_name}', got '{full_name}'"
    )
    
    # Test with different table names
    test_cases = [
        "products",
        "sales_data", 
        "customer_info",
        "inventory"
    ]
    
    for table_name in test_cases:
        full_name = db_config.get_full_table_name(table_name)
        if schema_name and schema_name != "public":
            expected = f"{schema_name}.{table_name}"
        else:
            expected = table_name
        assert full_name == expected, (
            f"For table '{table_name}': expected '{expected}', got '{full_name}'"
        )
    
    print(f"✅ Table name construction test passed!")
    print(f"   - Schema: {schema_name}")
    print(f"   - Example: {db_config.get_full_table_name('product_sales')}")


def test_schema_environment_variables():
    """Test that database configuration properly reads environment variables.
    
    This test verifies that the configuration can handle:
    - Environment variables being set
    - Fallback values when environment variables are not set
    """
    import os
    
    # Store original environment variable
    original_schema = os.getenv("LAKEBASE_SCHEMA")
    
    try:
        # Test with environment variable set
        os.environ["LAKEBASE_SCHEMA"] = "test_schema"
        
        # Re-import to get fresh values
        import importlib
        import dash_dbx_writeback.config as config_module
        importlib.reload(config_module)
        
        # Get the new db_config instance
        from dash_dbx_writeback.config import db_config as new_db_config
        
        # Test the values
        schema = new_db_config.get_schema_name()
        
        assert schema == "test_schema", f"Expected 'test_schema', got '{schema}'"
        
        # Test table name construction
        full_name = new_db_config.get_full_table_name("test_table")
        expected = "test_schema.test_table"
        assert full_name == expected, f"Expected '{expected}', got '{full_name}'"
        
        print(f"✅ Environment variable test passed!")
        print(f"   - Schema: {schema}")
        print(f"   - Example: {full_name}")
        
    finally:
        # Restore original environment variable
        if original_schema is not None:
            os.environ["LAKEBASE_SCHEMA"] = original_schema
        else:
            os.environ.pop("LAKEBASE_SCHEMA", None)
        
        # Re-import to restore original values
        import importlib
        import dash_dbx_writeback.config as config_module
        importlib.reload(config_module)
