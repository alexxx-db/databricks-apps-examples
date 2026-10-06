"""
Integration tests for PostgreSQL functionality with Databricks Lakebase.

These tests verify the end-to-end functionality of:
- Database connection pooling with OAuth authentication
- Table creation and schema management
- Data insertion and retrieval
- Query operations with parameterization
- Error handling and edge cases
"""

import pytest

# Needs a live Lakebase instance; CI runs `pytest -m "not integration"`
pytestmark = pytest.mark.integration
import pandas as pd
import datetime
from typing import List, Dict, Any

from dash_dbx_writeback.database_operations import (
    get_connection,
    initialize_connection_pool,
    close_all_connections,
    query_df,
    execute_sql,
    check_table_exists,
    create_table_from_dataframe,
    bulk_insert,
    read_table,
)
from dash_dbx_writeback.callbacks.tables import (
    initialize_table,
    insert_overwrite_table,
    ensure_table_exists,
)
from dash_dbx_writeback.config import db_config


# Use the session-scoped connection pool from conftest.py
# This ensures proper initialization and cleanup across all tests


@pytest.fixture
def test_table_name():
    """Generate unique test table name"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"test_table_{timestamp}"


@pytest.fixture
def test_schema():
    """Get test schema name"""
    return db_config.SCHEMA


@pytest.fixture
def full_test_table_name(test_schema, test_table_name):
    """Generate full table name with schema"""
    if test_schema and test_schema != "public":
        return f"{test_schema}.{test_table_name}"
    return test_table_name


@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for testing"""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "age": [25, 30, 35, 40, 45],
        "salary": [50000.0, 60000.0, 70000.0, 80000.0, 90000.0],
        "is_active": [True, True, False, True, False],
    })


@pytest.fixture
def product_dataframe():
    """Create product DataFrame similar to app data"""
    return pd.DataFrame({
        "LAYOUT_ID": ["LAY001", "LAY002", "LAY003"],
        "SELL_ID": ["SELL001", "SELL002", "SELL003"],
        "PRODUCT_NAME": ["Product A", "Product B", "Product C"],
        "LOYALTY_GROUP": ["Core", "Premium", "Core"],
        "SEGMENT_1": ["High Value", "Regular", "High Value"],
        "SEGMENT_2": ["Regular Shopper", "Family", "Regular Shopper"],
        "ORIGIN": ["AU", "AU", "NZ"],
        "CATEGORY_NAME": ["Dairy", "Bakery", "Meat"],
        "SUBCATEGORY_NAME": ["Milk", "Bread", "Beef"],
        "ITEM_CLASS_NAME": ["Full Cream", "White", "Steak"],
        "SUPPLIER": ["Supplier A", "Supplier B", "Supplier C"],
        "BRAND": ["Brand A", "Brand B", "Brand C"],
        "PACK_SIZE": ["2L", "650g", "500g"],
        "SHELF_SPACE_CM": [12.5, 15.0, 18.5],
    })


@pytest.fixture(autouse=True)
def cleanup_test_table(full_test_table_name):
    """Cleanup test table after each test"""
    yield
    
    # Drop test table if it exists
    try:
        execute_sql(f"DROP TABLE IF EXISTS {full_test_table_name}")
    except Exception:
        pass


class TestConnectionPooling:
    """Test database connection pool initialization and management"""
    
    def test_pg_connection_pool_initialization(self, pg_connection_pool):
        """Test that connection pool initializes successfully"""
        assert pg_connection_pool is not None
        assert pg_connection_pool.closed is False
    
    def test_get_connection(self, pg_connection_pool):
        """Test getting connection from pool"""
        pool = get_connection()
        assert pool is not None
        assert pool.closed is False
    
    def test_connection_reuse(self, pg_connection_pool):
        """Test that connections are reused from pool"""
        pool1 = get_connection()
        pool2 = get_connection()
        assert pool1 is pool2  # Should be same pool instance


class TestTableOperations:
    """Test table creation, existence checking, and schema operations"""
    
    def test_check_table_exists_nonexistent(self, pg_connection_pool, full_test_table_name):
        """Test checking for non-existent table"""
        exists = check_table_exists(full_test_table_name)
        assert exists is False
    
    def test_create_table_from_dataframe(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test creating table from DataFrame schema"""
        success = create_table_from_dataframe(full_test_table_name, sample_dataframe)
        assert success is True
        
        # Verify table exists
        exists = check_table_exists(full_test_table_name)
        assert exists is True
    
    def test_check_table_exists_existing(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test checking for existing table"""
        # Create table
        create_table_from_dataframe(full_test_table_name, sample_dataframe)
        
        # Check existence
        exists = check_table_exists(full_test_table_name)
        assert exists is True
    
    def test_table_name_with_schema(self, pg_connection_pool, test_table_name):
        """Test table name parsing with explicit schema"""
        schema = db_config.SCHEMA
        full_name = f"{schema}.{test_table_name}"
        
        # Create table
        df = pd.DataFrame({"col1": [1, 2, 3]})
        create_table_from_dataframe(full_name, df)
        
        # Check with full name
        exists = check_table_exists(full_name)
        assert exists is True
        
        # Cleanup
        execute_sql(f"DROP TABLE IF EXISTS {full_name}")
    
    def test_ensure_table_exists_creates_new(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test ensure_table_exists creates table if it doesn't exist"""
        from dash_dbx_writeback.callbacks.tables import ensure_table_exists
        
        with pg_connection_pool.connection() as conn:
            existed = ensure_table_exists(full_test_table_name, sample_dataframe, conn)
        
        assert existed is False  # Table didn't exist before
        
        # Verify table was created
        exists = check_table_exists(full_test_table_name)
        assert exists is True
    
    def test_ensure_table_exists_existing_table(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test ensure_table_exists with existing table"""
        from dash_dbx_writeback.callbacks.tables import ensure_table_exists
        
        # Create table first
        create_table_from_dataframe(full_test_table_name, sample_dataframe)
        
        # Call ensure_table_exists
        with pg_connection_pool.connection() as conn:
            existed = ensure_table_exists(full_test_table_name, sample_dataframe, conn)
        
        assert existed is True  # Table already existed


class TestDataInsertion:
    """Test data insertion operations"""
    
    def test_bulk_insert_new_table(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test bulk insert into new table"""
        result = bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        
        assert isinstance(result, int)
        assert result == len(sample_dataframe)
        
        # Verify data was inserted
        df = read_table(full_test_table_name)
        assert len(df) == len(sample_dataframe)
        assert list(df["name"]) == list(sample_dataframe["name"])
    
    def test_bulk_insert_overwrite(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test bulk insert with overwrite mode"""
        # Insert initial data
        bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        
        # Insert new data with overwrite
        new_data = pd.DataFrame({
            "id": [10, 20],
            "name": ["New1", "New2"],
            "age": [25, 30],
            "salary": [50000.0, 60000.0],
            "is_active": [True, False],
        })
        
        result = bulk_insert(full_test_table_name, new_data, overwrite=True)
        assert result == len(new_data)
        
        # Verify only new data exists
        df = read_table(full_test_table_name)
        assert len(df) == len(new_data)
        assert list(df["name"]) == ["New1", "New2"]
    
    def test_bulk_insert_append(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test bulk insert in append mode"""
        # Insert initial data
        bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        
        # Append more data
        new_data = pd.DataFrame({
            "id": [6, 7],
            "name": ["Frank", "Grace"],
            "age": [50, 55],
            "salary": [100000.0, 110000.0],
            "is_active": [True, True],
        })
        
        result = bulk_insert(full_test_table_name, new_data, overwrite=False)
        assert result == len(new_data)
        
        # Verify all data exists
        df = read_table(full_test_table_name)
        assert len(df) == len(sample_dataframe) + len(new_data)
    
    def test_insert_overwrite_table(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test insert_overwrite_table function from callbacks"""
        result = insert_overwrite_table(
            table_name=full_test_table_name,
            df=sample_dataframe,
            conn=pg_connection_pool,
            overwrite=True
        )
        
        assert isinstance(result, int)
        assert result > 0
        
        # Verify data
        df = read_table(full_test_table_name)
        assert len(df) == len(sample_dataframe)
    
    def test_insert_with_null_values(self, pg_connection_pool, full_test_table_name):
        """Test inserting data with NULL values"""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", None, "Charlie"],
            "age": [25, 30, None],
        })
        
        result = bulk_insert(full_test_table_name, df, overwrite=False)
        assert result == len(df)
        
        # Verify NULL values are preserved
        retrieved = read_table(full_test_table_name)
        assert pd.isna(retrieved.loc[1, "name"])
        assert pd.isna(retrieved.loc[2, "age"])


class TestDataRetrieval:
    """Test data query and retrieval operations"""
    
    def test_query_df_basic(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test basic query_df operation"""
        # Insert data
        bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        
        # Query all data
        df = query_df(f"SELECT * FROM {full_test_table_name}")
        
        assert len(df) == len(sample_dataframe)
        assert "name" in df.columns
        assert "age" in df.columns
    
    def test_query_df_with_where_clause(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test query_df with WHERE clause"""
        # Insert data
        bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        
        # Query with condition
        df = query_df(f'SELECT * FROM {full_test_table_name} WHERE age > 30')
        
        assert len(df) == 3  # Bob, Charlie, David, Eve with age > 30
        assert all(df["age"] > 30)
    
    def test_query_df_parameterized(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test parameterized query to prevent SQL injection"""
        # Insert data
        bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        
        # Parameterized query
        df = query_df(
            f'SELECT * FROM {full_test_table_name} WHERE name = %s',
            params=("Alice",)
        )
        
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Alice"
        assert df.iloc[0]["age"] == 25
    
    def test_query_df_multiple_parameters(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test query with multiple parameters"""
        # Insert data
        bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        
        # Query with multiple params
        df = query_df(
            f'SELECT * FROM {full_test_table_name} WHERE age >= %s AND age <= %s',
            params=(30, 40)
        )
        
        assert len(df) == 3  # Bob (30), Charlie (35), David (40)
        assert all((df["age"] >= 30) & (df["age"] <= 40))
    
    def test_read_table(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test read_table function"""
        # Insert data
        bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        
        # Read table
        df = read_table(full_test_table_name)
        
        assert len(df) == len(sample_dataframe)
        assert list(df.columns) == list(sample_dataframe.columns)
    
    def test_read_table_with_limit(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test read_table with limit parameter"""
        # Insert data
        bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        
        # Read with limit
        df = read_table(full_test_table_name, limit=3)
        
        assert len(df) == 3
    
    def test_query_empty_result(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test query that returns empty result"""
        # Insert data
        bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        
        # Query that returns no rows
        df = query_df(f'SELECT * FROM {full_test_table_name} WHERE age > 1000')
        
        assert len(df) == 0
        assert isinstance(df, pd.DataFrame)


class TestDataTypes:
    """Test different data types in PostgreSQL"""
    
    def test_integer_types(self, pg_connection_pool, full_test_table_name):
        """Test integer data types"""
        df = pd.DataFrame({
            "small_int": [1, 2, 3],
            "big_int": [1000000, 2000000, 3000000],
        })
        
        result = bulk_insert(full_test_table_name, df, overwrite=False)
        assert result == len(df)
        
        retrieved = read_table(full_test_table_name)
        assert retrieved["small_int"].dtype == "int64"
        assert list(retrieved["big_int"]) == list(df["big_int"])
    
    def test_float_types(self, pg_connection_pool, full_test_table_name):
        """Test float/double precision types"""
        df = pd.DataFrame({
            "price": [10.99, 20.50, 30.25],
            "rating": [4.5, 3.8, 4.9],
        })
        
        result = bulk_insert(full_test_table_name, df, overwrite=False)
        assert result == len(df)
        
        retrieved = read_table(full_test_table_name)
        assert retrieved["price"].dtype == "float64"
        assert abs(retrieved["rating"].iloc[0] - 4.5) < 0.001
    
    def test_boolean_types(self, pg_connection_pool, full_test_table_name):
        """Test boolean data types"""
        df = pd.DataFrame({
            "is_active": [True, False, True],
            "is_verified": [False, True, True],
        })
        
        result = bulk_insert(full_test_table_name, df, overwrite=False)
        assert result == len(df)
        
        retrieved = read_table(full_test_table_name)
        assert list(retrieved["is_active"]) == [True, False, True]
    
    def test_text_types(self, pg_connection_pool, full_test_table_name):
        """Test text/string data types"""
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "description": [
                "Short text",
                "A much longer description with special chars: !@#$%",
                "Unicode text: 日本語 中文 العربية"
            ],
        })
        
        result = bulk_insert(full_test_table_name, df, overwrite=False)
        assert result == len(df)
        
        retrieved = read_table(full_test_table_name)
        assert retrieved["description"].iloc[2] == "Unicode text: 日本語 中文 العربية"
    
    def test_mixed_types(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test DataFrame with mixed data types"""
        result = bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        assert result == len(sample_dataframe)
        
        retrieved = read_table(full_test_table_name)
        assert retrieved["id"].dtype == "int64"
        assert retrieved["salary"].dtype == "float64"
        assert retrieved["name"].dtype == "object"
        assert retrieved["is_active"].dtype == "bool"


class TestProductData:
    """Test operations with product data similar to application data"""
    
    def test_initialize_table_with_product_data(self, pg_connection_pool, test_table_name):
        """Test initializing table with product data"""
        # initialize_table expects table name without schema prefix
        # It will call db_config.get_full_table_name internally
        result = initialize_table(test_table_name, pg_connection_pool)
        
        assert result > 0
        
        # Verify data - need to use full table name for read_table
        full_table_name = db_config.get_full_table_name(test_table_name)
        df = read_table(full_table_name)
        assert len(df) > 0
        assert "PRODUCT_NAME" in df.columns
        assert "CATEGORY_NAME" in df.columns
        
        # Cleanup
        execute_sql(f"DROP TABLE IF EXISTS {full_table_name}")
    
    def test_product_data_insertion(self, pg_connection_pool, full_test_table_name, product_dataframe):
        """Test inserting product-like data"""
        result = bulk_insert(full_test_table_name, product_dataframe, overwrite=False)
        
        assert result == len(product_dataframe)
        
        # Verify data
        df = read_table(full_test_table_name)
        assert len(df) == len(product_dataframe)
        assert list(df["LAYOUT_ID"]) == list(product_dataframe["LAYOUT_ID"])
    
    def test_query_by_category(self, pg_connection_pool, full_test_table_name, product_dataframe):
        """Test querying products by category (like app functionality)"""
        # Insert data
        bulk_insert(full_test_table_name, product_dataframe, overwrite=False)
        
        # Query by category
        df = query_df(
            f'SELECT * FROM {full_test_table_name} WHERE "CATEGORY_NAME" = %s',
            params=("Dairy",)
        )
        
        assert len(df) == 1
        assert df.iloc[0]["PRODUCT_NAME"] == "Product A"
    
    def test_filter_multiple_categories(self, pg_connection_pool, full_test_table_name, product_dataframe):
        """Test filtering by multiple categories"""
        # Insert data
        bulk_insert(full_test_table_name, product_dataframe, overwrite=False)
        
        # Query multiple categories
        df = query_df(
            f'SELECT * FROM {full_test_table_name} WHERE "CATEGORY_NAME" IN (%s, %s)',
            params=("Dairy", "Bakery")
        )
        
        assert len(df) == 2
        categories = list(df["CATEGORY_NAME"])
        assert "Dairy" in categories
        assert "Bakery" in categories


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_query_invalid_table(self, pg_connection_pool):
        """Test querying non-existent table returns empty DataFrame"""
        df = query_df("SELECT * FROM nonexistent_table_xyz")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_insert_to_invalid_table_creates_table(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test that bulk_insert creates table if it doesn't exist"""
        # Don't create table first
        result = bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        
        assert result == len(sample_dataframe)
        
        # Verify table was created
        exists = check_table_exists(full_test_table_name)
        assert exists is True
    
    def test_empty_dataframe_insert(self, pg_connection_pool, full_test_table_name):
        """Test inserting empty DataFrame"""
        df = pd.DataFrame({"col1": [], "col2": []})
        
        result = bulk_insert(full_test_table_name, df, overwrite=False)
        
        # Should create table but insert 0 rows
        assert result == 0
        assert check_table_exists(full_test_table_name)
    
    def test_special_characters_in_column_names(self, pg_connection_pool, full_test_table_name):
        """Test handling special characters in column names"""
        df = pd.DataFrame({
            "COLUMN_WITH_UNDERSCORE": [1, 2, 3],
            "Column With Spaces": ["a", "b", "c"],  # Should be quoted
        })
        
        result = bulk_insert(full_test_table_name, df, overwrite=False)
        assert result == len(df)
        
        # Verify data retrieval
        retrieved = read_table(full_test_table_name)
        assert len(retrieved) == len(df)


class TestConnectionLifecycle:
    """Test connection pool lifecycle and cleanup"""
    
    def test_close_and_reinitialize(self, pg_connection_pool):
        """Test closing and reinitializing connection pool"""
        # Get initial connection
        pool1 = get_connection()
        assert pool1 is not None
        
        # Close connections
        close_all_connections()
        
        # Reinitialize
        success = initialize_connection_pool()
        assert success is True
        
        # Get new connection
        pool2 = get_connection()
        assert pool2 is not None
    
    def test_multiple_operations_same_connection(self, pg_connection_pool, full_test_table_name, sample_dataframe):
        """Test multiple operations using same connection pool"""
        # Multiple operations
        bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
        df1 = read_table(full_test_table_name)
        df2 = query_df(f"SELECT COUNT(*) as cnt FROM {full_test_table_name}")
        exists = check_table_exists(full_test_table_name)
        
        assert len(df1) == len(sample_dataframe)
        assert df2.iloc[0]["cnt"] == len(sample_dataframe)
        assert exists is True


@pytest.mark.integration
class TestEndToEndScenarios:
    """Test end-to-end application scenarios"""
    
    def test_forecast_submission_workflow(self, pg_connection_pool):
        """Test complete forecast submission workflow"""
        # Simulate forecast submission
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        table_name = f"test_forecast_submissions_{timestamp}"
        full_table_name = db_config.get_full_table_name(table_name)
        
        try:
            # Create forecast data
            forecast_id = f"FCST-{timestamp}"
            df = pd.DataFrame({
                "FORECAST_ID": [forecast_id] * 3,
                "PRODUCT_NAME": ["Product A", "Product B", "Product C"],
                "FORECAST_VALUE": [100.5, 200.75, 150.25],
                "SUBMISSION_TIMESTAMP": [datetime.datetime.now().isoformat()] * 3,
            })
            
            # Insert data
            result = bulk_insert(full_table_name, df, overwrite=False)
            assert result == len(df)
            
            # Query back the forecast
            retrieved = query_df(
                f'SELECT * FROM {full_table_name} WHERE "FORECAST_ID" = %s',
                params=(forecast_id,)
            )
            
            assert len(retrieved) == 3
            assert list(retrieved["FORECAST_ID"]) == [forecast_id] * 3
            
        finally:
            # Cleanup
            execute_sql(f"DROP TABLE IF EXISTS {full_table_name}")
    
    def test_category_filtering_workflow(self, pg_connection_pool, product_dataframe):
        """Test category filtering workflow like in the application"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        table_name = f"test_layout_data_{timestamp}"
        full_table_name = db_config.get_full_table_name(table_name)
        
        try:
            # Insert product data
            bulk_insert(full_table_name, product_dataframe, overwrite=False)
            
            # Test filtering by different categories
            categories = ["Dairy", "Bakery", "Meat"]
            
            for category in categories:
                df = query_df(
                    f'SELECT * FROM {full_table_name} WHERE "CATEGORY_NAME" = %s',
                    params=(category,)
                )
                assert len(df) == 1
                assert df.iloc[0]["CATEGORY_NAME"] == category
            
            # Test "All" categories
            df_all = read_table(full_table_name)
            assert len(df_all) == len(product_dataframe)
            
        finally:
            # Cleanup
            execute_sql(f"DROP TABLE IF EXISTS {full_table_name}")
    
    def test_data_update_workflow(self, pg_connection_pool):
        """Test data update workflow (overwrite vs append)"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        table_name = f"test_update_{timestamp}"
        full_table_name = db_config.get_full_table_name(table_name)
        
        try:
            # Initial data
            df1 = pd.DataFrame({
                "id": [1, 2, 3],
                "value": ["a", "b", "c"],
            })
            
            bulk_insert(full_table_name, df1, overwrite=False)
            assert len(read_table(full_table_name)) == 3
            
            # Append mode
            df2 = pd.DataFrame({
                "id": [4, 5],
                "value": ["d", "e"],
            })
            
            bulk_insert(full_table_name, df2, overwrite=False)
            assert len(read_table(full_table_name)) == 5
            
            # Overwrite mode
            df3 = pd.DataFrame({
                "id": [10],
                "value": ["z"],
            })
            
            bulk_insert(full_table_name, df3, overwrite=True)
            result = read_table(full_table_name)
            assert len(result) == 1
            assert result.iloc[0]["value"] == "z"
            
        finally:
            # Cleanup
            execute_sql(f"DROP TABLE IF EXISTS {full_table_name}")

