#!/usr/bin/env python3
"""
Setup script to create a dedicated test database in Databricks Lakebase.

This script creates a separate database for testing to ensure complete
isolation from production data.

Usage:
    python tests/setup_test_database.py
    
Environment Variables:
    LAKEBASE_INSTANCE_NAME - Your Lakebase instance name (required)
    LAKEBASE_TEST_DATABASE - Test database name (default: databricks_postgres_test)
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
import psycopg
import uuid


# Load environment variables
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✓ Loaded environment variables from {env_path}")


def log(message: str, level: str = "INFO") -> None:
    """Print formatted log message"""
    symbols = {
        "INFO": "ℹ️ ",
        "SUCCESS": "✓",
        "ERROR": "✗",
        "WARNING": "⚠️ ",
        "STEP": "→",
    }
    symbol = symbols.get(level, "  ")
    print(f"{symbol} {message}")


class TestDatabaseSetup:
    """Setup and manage test database for Lakebase"""
    
    def __init__(self):
        self.instance_name = os.getenv("LAKEBASE_INSTANCE_NAME")
        self.prod_database = os.getenv("LAKEBASE_DATABASE", "databricks_postgres")
        self.test_database = os.getenv("LAKEBASE_TEST_DATABASE", f"{self.prod_database}_test")
        self.workspace_client = None
        self.host = None
        self.user = None
        
    def validate_config(self) -> bool:
        """Validate required configuration"""
        log("Validating configuration...", "STEP")
        
        if not self.instance_name:
            log("LAKEBASE_INSTANCE_NAME not set in environment", "ERROR")
            log("Please set it in your .env file or environment", "WARNING")
            return False
        
        log(f"Instance: {self.instance_name}", "INFO")
        log(f"Production database: {self.prod_database}", "INFO")
        log(f"Test database: {self.test_database}", "INFO")
        
        return True
    
    def initialize_workspace_client(self) -> bool:
        """Initialize Databricks workspace client"""
        log("Initializing Databricks workspace client...", "STEP")
        
        try:
            self.workspace_client = WorkspaceClient()
            log("Workspace client initialized", "SUCCESS")
            return True
        except Exception as e:
            log(f"Failed to initialize workspace client: {e}", "ERROR")
            return False
    
    def get_database_host(self) -> bool:
        """Get database host from Lakebase instance"""
        log("Retrieving database host...", "STEP")
        
        try:
            instance = self.workspace_client.database.get_database_instance(
                name=self.instance_name
            )
            self.host = instance.read_write_dns
            self.user = self.workspace_client.current_user.me().user_name
            
            log(f"Host: {self.host}", "INFO")
            log(f"User: {self.user}", "INFO")
            return True
        except Exception as e:
            log(f"Failed to get database host: {e}", "ERROR")
            return False
    
    def get_oauth_token(self) -> str:
        """Generate OAuth token for database connection"""
        token = self.workspace_client.database.generate_database_credential(
            request_id=str(uuid.uuid4()),
            instance_names=[self.instance_name]
        ).token
        return token
    
    def create_connection(self, database: str) -> psycopg.Connection:
        """Create a psycopg connection to the specified database"""
        token = self.get_oauth_token()
        
        conn = psycopg.connect(
            host=self.host,
            dbname=database,
            user=self.user,
            password=token,
            sslmode="require"
        )
        return conn
    
    def check_database_exists(self) -> bool:
        """Check if test database already exists"""
        log(f"Checking if database '{self.test_database}' exists...", "STEP")
        
        try:
            # Connect to production database to check
            conn = self.create_connection(self.prod_database)
            
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (self.test_database,)
                )
                exists = cur.fetchone() is not None
            
            conn.close()
            
            if exists:
                log(f"Database '{self.test_database}' already exists", "WARNING")
            else:
                log(f"Database '{self.test_database}' does not exist", "INFO")
            
            return exists
        except Exception as e:
            log(f"Error checking database existence: {e}", "ERROR")
            return False
    
    def create_database(self) -> bool:
        """Create the test database"""
        log(f"Creating database '{self.test_database}'...", "STEP")
        
        try:
            # Connect to production database to create new database
            conn = self.create_connection(self.prod_database)
            
            # Must set autocommit for CREATE DATABASE
            conn.autocommit = True
            
            with conn.cursor() as cur:
                # Create database
                cur.execute(f'CREATE DATABASE "{self.test_database}"')
                log(f"Database '{self.test_database}' created successfully", "SUCCESS")
            
            conn.close()
            return True
        except Exception as e:
            log(f"Error creating database: {e}", "ERROR")
            return False
    
    def create_test_schema(self) -> bool:
        """Create test schema in the test database"""
        log("Creating default test schema...", "STEP")
        
        try:
            # Connect to the new test database
            conn = self.create_connection(self.test_database)
            
            with conn.cursor() as cur:
                # Create test schema
                cur.execute("CREATE SCHEMA IF NOT EXISTS test_schema")
                log("Schema 'test_schema' created", "SUCCESS")
                
                # Grant necessary permissions (quote username to handle special chars like @)
                cur.execute(f'GRANT ALL PRIVILEGES ON SCHEMA test_schema TO "{self.user}"')
                log("Permissions granted", "SUCCESS")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log(f"Error creating schema: {e}", "ERROR")
            return False
    
    def verify_setup(self) -> bool:
        """Verify the test database setup"""
        log("Verifying test database setup...", "STEP")
        
        try:
            # Connect to test database
            conn = self.create_connection(self.test_database)
            
            with conn.cursor() as cur:
                # Check database connection
                cur.execute("SELECT current_database(), current_user")
                db_name, user = cur.fetchone()
                log(f"Connected to database: {db_name}", "SUCCESS")
                log(f"Connected as user: {user}", "SUCCESS")
                
                # Check schema exists
                cur.execute(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'test_schema'"
                )
                schema_exists = cur.fetchone() is not None
                
                if schema_exists:
                    log("Schema 'test_schema' verified", "SUCCESS")
                else:
                    log("Schema 'test_schema' not found", "WARNING")
                    return False
                
                # Create a test table to verify permissions
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS test_schema.setup_verification (
                        id SERIAL PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                log("Test table created successfully", "SUCCESS")
                
                # Insert test data
                cur.execute("INSERT INTO test_schema.setup_verification DEFAULT VALUES")
                log("Test insert successful", "SUCCESS")
                
                # Drop test table
                cur.execute("DROP TABLE test_schema.setup_verification")
                log("Test cleanup successful", "SUCCESS")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log(f"Verification failed: {e}", "ERROR")
            return False
    
    def update_env_file(self) -> None:
        """Suggest updates to .env file"""
        log("\n" + "=" * 60, "INFO")
        log("CONFIGURATION", "INFO")
        log("=" * 60, "INFO")
        
        print("\nTo use the test database, add this to your .env file:")
        print(f"\n# Test Database Configuration")
        print(f"LAKEBASE_TEST_DATABASE={self.test_database}")
        
        print("\n" + "-" * 60)
        print("\nOr set it as an environment variable:")
        print(f"export LAKEBASE_TEST_DATABASE={self.test_database}")
        
        print("\n" + "-" * 60)
        print("\nThe tests will automatically use this test database")
        print("when LAKEBASE_TEST_DATABASE is set, keeping production safe!")
    
    def run(self) -> bool:
        """Run the complete setup process"""
        log("\n" + "=" * 60, "INFO")
        log("TEST DATABASE SETUP", "INFO")
        log("=" * 60 + "\n", "INFO")
        
        # Validate configuration
        if not self.validate_config():
            return False
        
        print()
        
        # Initialize workspace client
        if not self.initialize_workspace_client():
            return False
        
        print()
        
        # Get database host
        if not self.get_database_host():
            return False
        
        print()
        
        # Check if database exists
        exists = self.check_database_exists()
        
        print()
        
        if exists:
            log("Database already exists. Skipping creation.", "WARNING")
            user_input = input("\nDo you want to recreate it? This will DROP all test data! (yes/no): ")
            if user_input.lower() != "yes":
                log("Setup cancelled", "WARNING")
                
                # Still try to create schema and verify
                print()
                self.create_test_schema()
                print()
                success = self.verify_setup()
                
                if success:
                    print()
                    self.update_env_file()
                
                return success
            
            # Drop existing database
            log(f"Dropping existing database '{self.test_database}'...", "STEP")
            try:
                conn = self.create_connection(self.prod_database)
                conn.autocommit = True
                
                # Terminate existing connections
                with conn.cursor() as cur:
                    cur.execute(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{self.test_database}'
                        AND pid <> pg_backend_pid()
                    """)
                    cur.execute(f'DROP DATABASE IF EXISTS "{self.test_database}"')
                    log(f"Database dropped", "SUCCESS")
                
                conn.close()
            except Exception as e:
                log(f"Error dropping database: {e}", "ERROR")
                return False
            
            print()
        
        # Create database
        if not self.create_database():
            return False
        
        print()
        
        # Create test schema
        if not self.create_test_schema():
            return False
        
        print()
        
        # Verify setup
        success = self.verify_setup()
        
        if success:
            log("\n" + "=" * 60, "SUCCESS")
            log("TEST DATABASE SETUP COMPLETE!", "SUCCESS")
            log("=" * 60, "SUCCESS")
            
            print()
            self.update_env_file()
        
        return success


def main():
    """Main entry point"""
    setup = TestDatabaseSetup()
    
    try:
        success = setup.run()
        
        if success:
            print("\n" + "=" * 60)
            print("✓ Setup completed successfully!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("✗ Setup failed. Please check the errors above.")
            print("=" * 60)
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

