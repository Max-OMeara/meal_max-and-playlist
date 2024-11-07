import pytest
from unittest.mock import Mock, patch
from contextlib import contextmanager
import sqlite3
import re
from meal_max.models.kitchen_model import (
    create_meal,
    get_meal_by_id,
    get_meal_by_name,
    clear_meals,
    delete_meal,
    get_leaderboard,
    update_meal_stats,
    Meal
)

from meal_max.utils.sql_utils import get_db_connection


######################################################
#
#    Fixtures and Helper Functions
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Set up the in-memory database and create the 'meals' table."""
    create_table_script = """
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY,
        meal TEXT NOT NULL UNIQUE,
        cuisine TEXT NOT NULL,
        price REAL NOT NULL,
        difficulty TEXT NOT NULL,
        deleted BOOLEAN DEFAULT FALSE,
        battles INTEGER DEFAULT 0,
        wins INTEGER DEFAULT 0
    );
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript(create_table_script)
        conn.commit()



# Mocking the database connection for tests
@pytest.fixture
def mock_cursor(mocker):
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()

    # Mock the connection's cursor
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # Default return for queries
    mock_cursor.fetchall.return_value = []
    mock_conn.commit.return_value = None

    # Mock the get_db_connection context manager from sql_utils
    @contextmanager
    def mock_get_db_connection():
        yield mock_conn  # Yield the mocked connection object

    mocker.patch("meal_max.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test


######################################################
#
#    Create and Delete Meal Test Cases
#
######################################################

def test_create_meal(mock_cursor):
    """Test creating a new meal."""
    # Call the function to create a new meal
    create_meal("Burger", "American", 12.0, "HIGH")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]
    expected_arguments = ("Burger", "American", 12.0, "HIGH")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_duplicate_meal(mock_cursor):
    """Test error when creating a duplicate meal."""
    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("Meal with name 'Pizza' already exists")

    with pytest.raises(ValueError, match="Meal with name 'Pizza' already exists"):
        create_meal("Pizza", "Italian", 10.0, "LOW")

def test_create_meal_invalid_price():
    """Test creating a meal with an invalid price."""
    # Negative price
    with pytest.raises(ValueError, match="Invalid price: -10.0. Price must be a positive number."):
        create_meal("Steak", "American", -10.0, "MED")

    # Zero price
    with pytest.raises(ValueError, match="Invalid price: 0.0. Price must be a positive number."):
        create_meal("Salad", "Healthy", 0.0, "LOW")

def test_create_meal_invalid_difficulty():
    """Test creating a meal with an invalid difficulty level."""
    with pytest.raises(ValueError, match="Invalid difficulty level: EASY. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal("Soup", "French", 8.0, "EASY")

def test_delete_meal(mock_cursor):
    """Test deleting a meal."""
    # Simulate that the meal exists and is not deleted
    mock_cursor.fetchone.return_value = [False]

    delete_meal(1)

    expected_select_sql = normalize_whitespace("SELECT deleted FROM meals WHERE id = ?")
    expected_update_sql = normalize_whitespace("UPDATE meals SET deleted = TRUE WHERE id = ?")

    actual_select_sql = normalize_whitespace(mock_cursor.execute.call_args_list[0][0][0])
    actual_update_sql = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_select_sql == expected_select_sql, "The SELECT query did not match the expected structure."
    assert actual_update_sql == expected_update_sql, "The UPDATE query did not match the expected structure."

def test_delete_meal_invalid_id(mock_cursor):
    """Test error when trying to delete a non-existent meal."""
    # Simulate that no meal exists with the given ID
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        delete_meal(999)

def test_delete_meal_already_deleted(mock_cursor):
    """Test error when trying to delete a meal that's already marked as deleted."""
    # Simulate that the meal is already deleted
    mock_cursor.fetchone.return_value = [True]

    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        delete_meal(1)

def test_clear_meals(mock_cursor, mocker):
    """Test clearing the entire meals table."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_meal_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="DROP TABLE IF EXISTS meals; CREATE TABLE meals (...);"))

    # Call the clear_meals function
    clear_meals()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_meal_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once_with("DROP TABLE IF EXISTS meals; CREATE TABLE meals (...);")


######################################################
#
#    Retrieve Meal Test Cases
#
######################################################

def test_get_meal_by_id(mock_cursor):
    """Test retrieving a meal by ID."""
    # Simulate that the meal exists and is not deleted
    mock_cursor.fetchone.return_value = (1, "Pizza", "Italian", 10.0, "LOW", False)

    meal = get_meal_by_id(1)
    expected_meal = Meal(1, "Pizza", "Italian", 10.0, "LOW")
    assert meal == expected_meal, f"Expected {expected_meal}, got {meal}"

def test_get_meal_by_id_not_found(mock_cursor):
    """Test retrieving a meal by an ID that does not exist."""
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        get_meal_by_id(999)

def test_get_meal_by_id_deleted(mock_cursor):
    """Test retrieving a meal that has been deleted."""
    # Simulate that the meal is deleted
    mock_cursor.fetchone.return_value = (1, "Pizza", "Italian", 10.0, "LOW", True)

    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        get_meal_by_id(1)

def test_get_meal_by_name(mock_cursor):
    """Test retrieving a meal by name."""
    # Simulate that the meal exists
    mock_cursor.fetchone.return_value = (1, "Pizza", "Italian", 10.0, "LOW", False)

    meal = get_meal_by_name("Pizza")
    expected_meal = Meal(1, "Pizza", "Italian", 10.0, "LOW")
    assert meal == expected_meal, f"Expected {expected_meal}, got {meal}"

def test_get_meal_by_name_not_found(mock_cursor):
    """Test retrieving a meal by name that does not exist."""
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Meal with name Pizza not found"):
        get_meal_by_name("Pizza")

######################################################
#
#    Update Meal Stats Test Cases
#
######################################################

def test_update_meal_stats(mock_cursor):
    """Test updating meal statistics."""
    # Simulate that the meal exists and is not deleted
    mock_cursor.fetchone.return_value = [False]

    update_meal_stats(1, 'win')

    expected_query = normalize_whitespace("UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?")
    actual_query = normalize_whitespace(mock_cursor.execute.call_args_list[1][0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_update_meal_stats_invalid_result(mock_cursor):
    """Test updating meal stats with an invalid result."""
    mock_cursor.fetchone.return_value = [False]

    with pytest.raises(ValueError, match="Invalid result: tie. Expected 'win' or 'loss'."):
        update_meal_stats(1, 'tie')

def test_update_meal_stats_deleted_meal(mock_cursor):
    """Test updating stats for a meal that has been deleted."""
    mock_cursor.fetchone.return_value = [True]

    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        update_meal_stats(1, 'win')

def test_update_meal_stats_not_found(mock_cursor):
    """Test updating stats for a meal that does not exist."""
    mock_cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="Meal with ID 999 not found"):
        update_meal_stats(999, 'win')

######################################################
#
#    Leaderboard Test Cases
#
######################################################

# test_kitchen_model.py

def test_get_leaderboard(mock_cursor):
    """Test retrieving the leaderboard sorted by win percentage."""
    # Simulate meals with battle stats
    mock_cursor.fetchall.return_value = [
        (2, "Sushi", "Japanese", 15.0, "MED", 5, 4, 0.8),
        (1, "Pizza", "Italian", 10.0, "LOW", 10, 6, 0.6),
        (3, "Burger", "American", 12.0, "HIGH", 8, 2, 0.25)
    ]

    leaderboard = get_leaderboard(sort_by='win_pct')

    expected_leaderboard = [
        {'id': 2, 'meal': 'Sushi', 'cuisine': 'Japanese', 'price': 15.0, 'difficulty': 'MED', 'battles': 5, 'wins': 4, 'win_pct': 80.0},
        {'id': 1, 'meal': 'Pizza', 'cuisine': 'Italian', 'price': 10.0, 'difficulty': 'LOW', 'battles': 10, 'wins': 6, 'win_pct': 60.0},
        {'id': 3, 'meal': 'Burger', 'cuisine': 'American', 'price': 12.0, 'difficulty': 'HIGH', 'battles': 8, 'wins': 2, 'win_pct': 25.0}
    ]

    assert leaderboard == expected_leaderboard, f"Expected {expected_leaderboard}, but got {leaderboard}"


def test_get_leaderboard_invalid_sort_by(mock_cursor):
    """Test retrieving the leaderboard with an invalid sort_by parameter."""
    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid_sort"):
        get_leaderboard(sort_by='invalid_sort')

def test_get_leaderboard_empty(mock_cursor, caplog):
    """Test retrieving the leaderboard when there are no meals with battles."""
    mock_cursor.fetchall.return_value = []

    leaderboard = get_leaderboard()
    assert leaderboard == [], f"Expected empty list, but got {leaderboard}"

    assert "Leaderboard retrieved successfully" in caplog.text, "Expected log message not found."

######################################################
#
#    Additional Test Cases
#
######################################################

def test_create_meal_invalid_types():
    """Test creating a meal with invalid types for parameters."""
    # Non-float price
    with pytest.raises(ValueError, match="Invalid price: cheap. Price must be a positive number."):
        create_meal("Pizza", "Italian", "cheap", "LOW")

    # Invalid difficulty
    with pytest.raises(ValueError, match="Invalid difficulty level: 789. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal("Pizza", "Italian", 10.0, 789)


def test_meal_dataclass_validation():
    """Test the Meal dataclass validation."""
    with pytest.raises(ValueError, match="Price must be a positive value."):
        Meal(1, "Pizza", "Italian", -10.0, "LOW")

    with pytest.raises(ValueError, match="Difficulty must be 'LOW', 'MED', or 'HIGH'."):
        Meal(1, "Pizza", "Italian", 10.0, "EASY")


