import psycopg2
from psycopg2 import OperationalError, errorcodes, errors

# --- Configuration for your PostgreSQL server ---
# These are typically system-wide settings, not something you create on the fly in a directory.
DB_HOST = "localhost" # Or your PostgreSQL server IP/hostname
DB_NAME = "db" # The database you want to create or connect to
DB_USER = "user"     # A PostgreSQL user with sufficient privileges
DB_PASSWORD = "password" # The password for the user
DEFAULT_DB = "postgres"       # The default database to connect to initially (usually 'postgres')

def create_database(db_name, user, password, host, port="5432"):
    """
    Connects to the default PostgreSQL database (e.g., 'postgres')
    and creates a new database if it doesn't exist.
    """
    try:
        # Connect to the default 'postgres' database to create a new one
        conn = psycopg2.connect(
            dbname=DEFAULT_DB,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.autocommit = True # Important for CREATE DATABASE statements

        cursor = conn.cursor()

        # Check if the database already exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()

        if not exists:
            print(f"Database '{db_name}' does not exist. Creating it now...")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"Database '{db_name}' created successfully.")
        else:
            print(f"Database '{db_name}' already exists.")

    except OperationalError as e:
        print(f"Error connecting to PostgreSQL or creating database: {e}")
        # Specific error for database already exists (though we check for it)
        if hasattr(e, 'pgcode') and e.pgcode == errorcodes.DUPLICATE_DATABASE:
            print(f"Database '{db_name}' already exists.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

def connect_and_create_table(db_name, user, password, host, port="5432"):
    """
    Connects to the specified database and creates a sample table.
    """
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.autocommit = True # For simplicity, but usually you'd commit transactions manually
        cursor = conn.cursor()

        table_name = "users"
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE
        );
        """
        cursor.execute(create_table_query)
        print(f"Table '{table_name}' created or already exists in '{db_name}'.")

        # Example: Insert some data
        insert_query = f"INSERT INTO {table_name} (name, email) VALUES (%s, %s) ON CONFLICT (email) DO NOTHING;"
        data_to_insert = [
            ("Alice", "alice@example.com"),
            ("Bob", "bob@example.com"),
            ("Alice", "alice@example.com") # This will be ignored due to ON CONFLICT
        ]
        cursor.executemany(insert_query, data_to_insert)
        print("Sample data inserted (if not already present).")

        # Example: Query data
        cursor.execute(f"SELECT id, name, email FROM {table_name};")
        rows = cursor.fetchall()
        print("\nData in 'users' table:")
        for row in rows:
            print(row)

    except OperationalError as e:
        print(f"Error connecting to PostgreSQL database '{db_name}': {e}")
        # Hint for common connection errors
        print("Please ensure PostgreSQL server is running and connection details are correct.")
        print(f"Is database '{db_name}' created? (Run create_database first if not)")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    # IMPORTANT: Before running this script:
    # 1. You must have PostgreSQL installed on your system.
    # 2. The PostgreSQL server must be running.
    # 3. You need a PostgreSQL user (e.g., 'postgres' user, or one you created)
    #    with privileges to create databases.
    # 4. Fill in your actual DB_USER and DB_PASSWORD.

    print("Attempting to create database (if it doesn't exist)...")
    create_database(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST)

    print("\nAttempting to connect to the database and create a table...")
    connect_and_create_table(DB_NAME, DB_USER, DB_PASSWORD, DB_HOST)

    print("\nScript finished.")
    print("To verify, you can connect to your PostgreSQL database using `psql` or a GUI tool.")