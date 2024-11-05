from contextlib import contextmanager
import re
import sqlite3

import pytest

from meal_max.meal_max.models.kitchen_model import (
    Meal,
    create_meal,
    clear_meals,
    get_leaderboard
)

######################################################
#
#    Fixtures
#
######################################################

def normalize_whitespace(sql_query: str) -> str:
    return re.sub(r'\s+', ' ', sql_query).strip()

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

    mocker.patch("meal_max.kitchen.models.kitchen_model.get_db_connection", mock_get_db_connection)

    return mock_cursor  # Return the mock cursor so we can set expectations per test

######################################################
#
#    Create and Clear Meals
#
######################################################

def test_create_meal(mock_cursor):
    """Test creating a new meal in the database."""

    # Call the function to create a new meal
    create_meal(meal="Pasta", cuisine="Italian", price=12.5, difficulty="MED")

    expected_query = normalize_whitespace("""
        INSERT INTO meals (meal, cuisine, price, difficulty)
        VALUES (?, ?, ?, ?)
    """)

    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    # Assert that the SQL query was correct
    assert actual_query == expected_query, "The SQL query did not match the expected structure."

    # Extract the arguments used in the SQL call
    actual_arguments = mock_cursor.execute.call_args[0][1]

    # Assert that the SQL query was executed with the correct arguments
    expected_arguments = ("Pasta", "Italian", 12.5, "MED")
    assert actual_arguments == expected_arguments, f"The SQL query arguments did not match. Expected {expected_arguments}, got {actual_arguments}."

def test_create_meal_duplicate(mock_cursor):
    """Test creating a meal with a duplicate name (should raise an error)."""

    # Simulate that the database will raise an IntegrityError due to a duplicate entry
    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed: meals.meal")

    # Expect the function to raise a ValueError with a specific message when handling the IntegrityError
    with pytest.raises(ValueError, match="Meal with name 'Pasta' already exists"):
        create_meal(meal="Pasta", cuisine="Italian", price=12.5, difficulty="MED")

def test_create_meal_invalid_price():
    """Test error when trying to create a meal with an invalid price."""

    # Attempt to create a meal with a negative price
    with pytest.raises(ValueError, match="Invalid price: -10.0. Price must be a positive number."):
        create_meal(meal="Pasta", cuisine="Italian", price=-10.0, difficulty="MED")

    # Attempt to create a meal with a non-numeric price
    with pytest.raises(ValueError, match="Invalid price: invalid. Price must be a positive number."):
        create_meal(meal="Pasta", cuisine="Italian", price="invalid", difficulty="MED")

def test_create_meal_invalid_difficulty():
    """Test error when trying to create a meal with an invalid difficulty level."""

    # Attempt to create a meal with an invalid difficulty
    with pytest.raises(ValueError, match="Invalid difficulty level: EXPERT. Must be 'LOW', 'MED', or 'HIGH'."):
        create_meal(meal="Pasta", cuisine="Italian", price=12.5, difficulty="EXPERT")

def test_clear_meals(mock_cursor, mocker):
    """Test clearing the entire meals database (recreating the meals table)."""

    # Mock the file reading
    mocker.patch.dict('os.environ', {'SQL_CREATE_TABLE_PATH': 'sql/create_meal_table.sql'})
    mock_open = mocker.patch('builtins.open', mocker.mock_open(read_data="The body of the create statement"))

    # Call the clear_meals function
    clear_meals()

    # Ensure the file was opened using the environment variable's path
    mock_open.assert_called_once_with('sql/create_meal_table.sql', 'r')

    # Verify that the correct SQL script was executed
    mock_cursor.executescript.assert_called_once_with("The body of the create statement")

######################################################
#
#    Get Leaderboard
#
######################################################

def test_get_leaderboard_sort_by_wins(mock_cursor):
    """Test retrieving the leaderboard sorted by wins."""

    # Simulate data in the database
    mock_cursor.fetchall.return_value = [
        (2, "Meal B", "Cuisine B", 15.0, "MED", 10, 7, 0.7),
        (3, "Meal C", "Cuisine C", 20.0, "HIGH", 8, 6, 0.75),
        (1, "Meal A", "Cuisine A", 10.0, "LOW", 5, 3, 0.6),
    ]

    # Call the get_leaderboard function
    leaderboard = get_leaderboard(sort_by="wins")

    # Expected result based on simulated data and sorting by wins
    expected_result = [
        {'id': 2, 'meal': 'Meal B', 'cuisine': 'Cuisine B', 'price': 15.0, 'difficulty': 'MED', 'battles': 10, 'wins': 7, 'win_pct': 70.0},
        {'id': 3, 'meal': 'Meal C', 'cuisine': 'Cuisine C', 'price': 20.0, 'difficulty': 'HIGH', 'battles': 8, 'wins': 6, 'win_pct': 75.0},
        {'id': 1, 'meal': 'Meal A', 'cuisine': 'Cuisine A', 'price': 10.0, 'difficulty': 'LOW', 'battles': 5, 'wins': 3, 'win_pct': 60.0},
    ]

    # Ensure the results match the expected output
    assert leaderboard == expected_result, f"Expected {expected_result}, but got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0
         ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_sort_by_win_pct(mock_cursor):
    """Test retrieving the leaderboard sorted by win percentage."""

    # Simulate data in the database
    mock_cursor.fetchall.return_value = [
        (3, "Meal C", "Cuisine C", 20.0, "HIGH", 8, 6, 0.75),
        (2, "Meal B", "Cuisine B", 15.0, "MED", 10, 7, 0.7),
        (1, "Meal A", "Cuisine A", 10.0, "LOW", 5, 3, 0.6),
    ]

    # Call the get_leaderboard function with sort_by='win_pct'
    leaderboard = get_leaderboard(sort_by="win_pct")

    # Expected result based on simulated data and sorting by win_pct
    expected_result = [
        {'id': 3, 'meal': 'Meal C', 'cuisine': 'Cuisine C', 'price': 20.0, 'difficulty': 'HIGH', 'battles': 8, 'wins': 6, 'win_pct': 75.0},
        {'id': 2, 'meal': 'Meal B', 'cuisine': 'Cuisine B', 'price': 15.0, 'difficulty': 'MED', 'battles': 10, 'wins': 7, 'win_pct': 70.0},
        {'id': 1, 'meal': 'Meal A', 'cuisine': 'Cuisine A', 'price': 10.0, 'difficulty': 'LOW', 'battles': 5, 'wins': 3, 'win_pct': 60.0},
    ]

    # Ensure the results match the expected output
    assert leaderboard == expected_result, f"Expected {expected_result}, but got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0
         ORDER BY win_pct DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."

def test_get_leaderboard_invalid_sort_by(mock_cursor):
    """Test that get_leaderboard raises an error with an invalid sort_by parameter."""

    with pytest.raises(ValueError, match="Invalid sort_by parameter: invalid_sort"):
        get_leaderboard(sort_by="invalid_sort")

def test_get_leaderboard_empty_table(mock_cursor, caplog):
    """Test that get_leaderboard returns an empty list when no meals are available."""

    # Simulate that there are no meals in the database
    mock_cursor.fetchall.return_value = []

    # Call the get_leaderboard function
    leaderboard = get_leaderboard()

    # Ensure the result is an empty list
    assert leaderboard == [], f"Expected empty list, but got {leaderboard}"

    # Ensure the SQL query was executed correctly
    expected_query = normalize_whitespace("""
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0
         ORDER BY wins DESC
    """)
    actual_query = normalize_whitespace(mock_cursor.execute.call_args[0][0])

    assert actual_query == expected_query, "The SQL query did not match the expected structure."
