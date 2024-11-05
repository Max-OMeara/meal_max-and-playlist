from dataclasses import dataclass
import logging
import os
import sqlite3
from typing import Any, List, Dict

from meal_max.utils.sql_utils import get_db_connection
from meal_max.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Meal:
    """
    A class to represent a meal.

    Attributes:
        id (int): The unique identifier for the meal.
        meal (str): The name of the meal.
        cuisine (str): The type of cuisine of the meal.
        price (float): The price of the meal.
        difficulty (str): The difficulty level of preparing the meal.
    """
    id: int
    meal: str
    cuisine: str
    price: float
    difficulty: str

    def __post_init__(self):
        """
        Validates the attributes of the Meal instance after initialization.

        Raises:
            ValueError: If the price is not positive or the difficulty is invalid.
        """
        if self.price < 0:
            raise ValueError("Price must be a positive value.")
        if self.difficulty not in ['LOW', 'MED', 'HIGH']:
            raise ValueError("Difficulty must be 'LOW', 'MED', or 'HIGH'.")


def create_meal(meal: str, cuisine: str, price: float, difficulty: str) -> None:
    """
    Adds a new meal to the database.

    Args:
        meal (str): The name of the meal.
        cuisine (str): The type of cuisine.
        price (float): The price of the meal.
        difficulty (str): The difficulty level of preparation.

    Raises:
        ValueError: If the price or difficulty level is invalid.
        sqlite3.IntegrityError: If a meal with the same name already exists.
        sqlite3.Error: For any other database errors.
    """
    if not isinstance(price, (int, float)) or price <= 0:
        raise ValueError(f"Invalid price: {price}. Price must be a positive number.")
    if difficulty not in ['LOW', 'MED', 'HIGH']:
        raise ValueError(f"Invalid difficulty level: {difficulty}. Must be 'LOW', 'MED', or 'HIGH'.")

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meals (meal, cuisine, price, difficulty)
                VALUES (?, ?, ?, ?)
            """, (meal, cuisine, price, difficulty))
            conn.commit()

            logger.info("Meal successfully added to the database: %s", meal)

    except sqlite3.IntegrityError:
        logger.error("Duplicate meal name: %s", meal)
        raise ValueError(f"Meal with name '{meal}' already exists")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def clear_meals() -> None:
    """
    Recreates the meals table, effectively deleting all meals.

    Raises:
        sqlite3.Error: If any database error occurs.
    """
    try:
        with open(os.getenv("SQL_CREATE_TABLE_PATH", "/app/sql/create_meal_table.sql"), "r") as fh:
            create_table_script = fh.read()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(create_table_script)
            conn.commit()

            logger.info("Meals cleared successfully.")

    except sqlite3.Error as e:
        logger.error("Database error while clearing meals: %s", str(e))
        raise e


def get_leaderboard(sort_by: str = "wins") -> List[Dict[str, Any]]:
    """
    Retrieves the leaderboard of meals based on battles or win percentage.

    Args:
        sort_by (str): The sorting criterion, either "wins" or "win_pct".

    Returns:
        List[Dict[str, Any]]: A list of meals with their statistics.

    Raises:
        ValueError: If the sorting criterion is invalid.
        sqlite3.Error: If any database error occurs.
    """
    query = """
        SELECT id, meal, cuisine, price, difficulty, battles, wins, (wins * 1.0 / battles) AS win_pct
        FROM meals WHERE deleted = false AND battles > 0
    """

    if sort_by == "win_pct":
        query += " ORDER BY win_pct DESC"
    elif sort_by == "wins":
        query += " ORDER BY wins DESC"
    else:
        logger.error("Invalid sort_by parameter: %s", sort_by)
        raise ValueError("Invalid sort_by parameter: %s" % sort_by)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        leaderboard = []
        for row in rows:
            meal = {
                'id': row[0],
                'meal': row[1],
                'cuisine': row[2],
                'price': row[3],
                'difficulty': row[4],
                'battles': row[5],
                'wins': row[6],
                'win_pct': round(row[7] * 100, 1)
            }
            leaderboard.append(meal)

        logger.info("Leaderboard retrieved successfully")
        return leaderboard

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e
