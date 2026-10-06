# Test Suite Documentation

## Overview

This directory contains comprehensive integration tests for the Databricks Lakebase PostgreSQL functionality. All tests run against the actual Lakebase database with OAuth authentication using the same `.env` configuration as the application.

## Test Files

### `test_postgresql_integration.py`

Comprehensive integration tests for PostgreSQL/Lakebase functionality covering:

- **Connection Pooling** - OAuth authentication, connection reuse, lifecycle management
- **Table Operations** - Creation, existence checking, schema management
- **Data Insertion** - Bulk insert, overwrite, append modes, NULL handling
- **Data Retrieval** - Queries, parameterization, filtering, pagination
- **Data Types** - Integer, float, boolean, text, mixed types
- **Product Data** - Application-specific data operations and workflows
- **Error Handling** - Invalid tables, empty data, edge cases
- **End-to-End Scenarios** - Complete workflows like forecast submission and category filtering

## Test Database Setup

### Option 1: Dedicated Test Database (Recommended)

Create a completely separate database for testing to ensure zero impact on production:

```bash
# Run the setup script
python tests/setup_test_database.py
```

This will:
- Create a new database (e.g., `databricks_postgres_test`)
- Set up test schema and permissions
- Verify the setup with test operations

Then add to your `.env`:
```bash
LAKEBASE_TEST_DATABASE=databricks_postgres_test
```

**Benefits:**
- ✅ Complete isolation from production
- ✅ No risk of impacting production data
- ✅ Can drop entire database for clean slate
- ✅ Better reflects production environment

### Option 2: Test Schema in Production Database

Tests will use a separate schema (`test_schema`) within the production database.

**When to Use:**
- Cannot create additional databases
- Want simpler setup
- Comfortable with schema-level isolation

## Running Tests

### Prerequisites

1. **Environment Setup**
   - Ensure `.env` file is configured with Lakebase credentials
   - Required environment variables:
     - `LAKEBASE_INSTANCE_NAME` - Your Lakebase instance name
     - `LAKEBASE_DATABASE` - Database name (default: `databricks_postgres`)
     - `LAKEBASE_TEST_DATABASE` - **Dedicated test database (recommended)**
     - `LAKEBASE_SCHEMA` - Schema for production (optional)
     - `LAKEBASE_TEST_SCHEMA` - Schema for tests (default: `test_schema`)

2. **Install Dependencies**
   ```bash
   uv pip install -e ".[dev]"
   ```

### Run All Tests

```bash
# Run all integration tests
uv run python -m pytest tests/test_postgresql_integration.py -v

# Run with detailed output
uv run python -m pytest tests/test_postgresql_integration.py -v --tb=short

# Run specific test class
uv run python -m pytest tests/test_postgresql_integration.py::TestConnectionPooling -v

# Run specific test
uv run python -m pytest tests/test_postgresql_integration.py::TestConnectionPooling::test_pg_connection_pool_initialization -v
```

### Run with Coverage

```bash
uv run python -m pytest tests/test_postgresql_integration.py --cov=dash_dbx_writeback --cov-report=html
```

### Run Integration Tests Only

```bash
# Using marker
uv run python -m pytest -m integration -v

# Everything that runs without a database (what CI runs)
uv run python -m pytest -m "not integration" -v

# By file pattern
uv run python -m pytest tests/test_postgresql_integration.py -v
```

## Test Configuration

### Test Schema Isolation

Tests use a separate schema (`test_schema` by default) to avoid impacting production data:

- **Automatic Setup**: Test schema is created automatically during test session initialization
- **Cleanup**: Test tables are cleaned up after each test
- **Optional Schema Cleanup**: Uncomment cleanup code in `conftest.py` to drop schema after tests

### Environment Variables

The test suite uses the following precedence for configuration:

1. `.env` file in project root (loaded automatically)
2. Environment variables set in shell
3. Test-specific overrides in `conftest.py`

**Test-Specific Variables:**
```bash
# Optional: Override schema for tests
export LAKEBASE_TEST_SCHEMA=my_test_schema
```

### Connection Pooling

- **Session-Scoped**: Single connection pool shared across all tests
- **OAuth Tokens**: Automatically rotated by psycopg3 connection class
- **Cleanup**: Automatically closed at end of test session

## Test Structure

### Test Classes

```python
TestConnectionPooling         # Connection pool lifecycle
TestTableOperations          # Table creation and management
TestDataInsertion            # Bulk insert operations
TestDataRetrieval            # Query and read operations
TestDataTypes                # Data type handling
TestProductData              # Application-specific operations
TestErrorHandling            # Edge cases and error scenarios
TestConnectionLifecycle      # Connection management
TestEndToEndScenarios        # Complete workflows
```

### Fixtures

**Session-Scoped:**
- `pg_connection_pool` - PostgreSQL connection pool
- `test_schema` - Test schema name

**Function-Scoped:**
- `test_table_name` - Unique table name per test
- `full_test_table_name` - Full table name with schema
- `sample_dataframe` - Generic test DataFrame
- `product_dataframe` - Product data similar to app
- `cleanup_test_table` - Automatic table cleanup

## Test Execution Flow

1. **pytest_configure**: Load `.env` file and set test configuration
2. **pytest_sessionstart**: Initialize connection pool and create test schema
3. **Test Execution**: Run tests with isolated tables
4. **Cleanup**: Drop test tables after each test
5. **pytest_sessionfinish**: Close connection pool (optionally drop schema)

## Test Results

### Example Output

```
============================================================
🚀 INITIALIZING TEST SESSION
============================================================
[2025-11-04 20:21:29.589] → Initializing Databricks Lakebase connection pool
[2025-11-04 20:21:29.589]   Instance: daveok
[2025-11-04 20:21:29.589]   Host: instance-xxx.database.azuredatabricks.net
[2025-11-04 20:21:29.589]   User: user@databricks.com
[2025-11-04 20:21:29.589]   Database: databricks_postgres
[2025-11-04 20:21:29.590] ✓ Lakebase connection pool initialized with OAuth authentication
✓ PostgreSQL connection pool initialized
✓ Test schema 'test_schema' ready
============================================================

======================== 39 passed in 141.09s ========================
```

## Troubleshooting

### Connection Issues

**Problem**: `LAKEBASE_INSTANCE_NAME not set`

**Solution**: 
- Verify `.env` file exists and contains `LAKEBASE_INSTANCE_NAME`
- Check file is not in `.gitignore` or `.cursorignore`
- Manually set environment variable: `export LAKEBASE_INSTANCE_NAME=your_instance`

### Permission Errors

**Problem**: `permission denied for schema test_schema`

**Solution**:
- Ensure your Databricks user has CREATE privileges on the database
- Use a schema you have permissions for: `export LAKEBASE_TEST_SCHEMA=your_schema`

### OAuth Token Errors

**Problem**: `Invalid OAuth token`

**Solution**:
- Verify Databricks CLI is configured: `databricks auth login`
- Check workspace client initialization in `database_operations.py`
- Token auto-rotation should handle expired tokens automatically

### Test Data Conflicts

**Problem**: Tests fail due to existing data

**Solution**:
- Tests use timestamp-based table names to avoid conflicts
- Each test cleans up its own tables
- Manually clean up if needed: `DROP SCHEMA test_schema CASCADE;`

## Best Practices

1. **Isolation**: Each test creates its own table with timestamp suffix
2. **Cleanup**: Use `cleanup_test_table` fixture for automatic cleanup
3. **Parameterization**: Use parameterized queries to prevent SQL injection
4. **Assertions**: Check both success conditions and data integrity
5. **Logging**: Tests produce detailed logs for debugging

## Adding New Tests

### Basic Template

```python
def test_my_feature(self, pg_connection_pool, full_test_table_name, sample_dataframe):
    """Test description"""
    # Setup
    bulk_insert(full_test_table_name, sample_dataframe, overwrite=False)
    
    # Execute
    result = my_function(full_test_table_name)
    
    # Assert
    assert result is not None
    assert result > 0
```

### Using Real Application Functions

```python
def test_app_workflow(self, pg_connection_pool, test_table_name):
    """Test actual application workflow"""
    from dash_dbx_writeback.database_operations import bulk_insert
    from dash_dbx_writeback.sample_data import INITIAL_DATA

    full_name = db_config.get_full_table_name(test_table_name)
    # Same helper the app uses; raises on failure
    assert bulk_insert(full_name, pd.DataFrame(INITIAL_DATA)) > 0

    # Cleanup
    execute_sql(f"DROP TABLE IF EXISTS {full_name}")
```

## Performance

- **Average Test Duration**: ~3.6 seconds per test
- **Total Suite Duration**: ~2.5 minutes for 39 tests
- **Database Operations**: Real OAuth tokens, actual database queries
- **Optimization**: Session-scoped connection pool reduces overhead

## Maintenance

### Regular Tasks

- Review and update test data fixtures
- Add tests for new features
- Monitor test execution time
- Update documentation

### Database Management

#### Dedicated Test Database

If you're using a dedicated test database, you can clean it up with:

```bash
# Drop the entire test database
python tests/cleanup_test_database.py
```

This will:
- Show database size and table count
- Require confirmation before deletion
- Terminate all active connections
- Drop the database completely

**Safety Features:**
- Refuses to drop production database
- Requires explicit confirmation (type "DELETE")
- Shows database size and table count before deletion

#### Test Schema in Production Database

Tests create tables in `test_schema` during execution. These are cleaned up automatically, but you can manually verify:

```sql
-- Check test tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'test_schema';

-- Clean up manually if needed
DROP SCHEMA test_schema CASCADE;
```

## Related Documentation

- **App setup and deployment**: [`../README.md`](../README.md)

---

**Last Updated**: November 4, 2025  
**Test Coverage**: Connection pooling, CRUD operations, OAuth authentication, data types, error handling, end-to-end workflows

