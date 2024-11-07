#!/bin/bash

# Define the absolute path to the project base directory
PROJECT_DIR="$(dirname "$0")/.."
DB_PATH="$PROJECT_DIR/db/meal_max.db"
SQL_FILE="$PROJECT_DIR/sql/create_meal_table.sql"

# Check if the database file already exists
if [ -f "$DB_PATH" ]; then
    echo "Recreating database at $DB_PATH."
    # Drop and recreate the tables
    sqlite3 "$DB_PATH" < "$SQL_FILE"
    echo "Database recreated successfully."
else
    echo "Creating database at $DB_PATH."
    # Create the database for the first time
    sqlite3 "$DB_PATH" < "$SQL_FILE"
    echo "Database created successfully."
fi
