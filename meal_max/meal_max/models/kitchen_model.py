from dataclasses import dataclass
import logging
import os
import sqlite3
from typing import Any

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
        if self.difficulty not in ["LOW", "MED", "HIGH"]:
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
    if difficulty not in ["LOW", "MED", "HIGH"]:
        raise ValueError(
            f"Invalid difficulty level: {difficulty}. Must be 'LOW', 'MED', or 'HIGH'."
        )

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO meals (meal, cuisine, price, difficulty)
                VALUES (?, ?, ?, ?)
            """,
                (meal, cuisine, price, difficulty),
            )
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
        with open(
            os.getenv("SQL_CREATE_TABLE_PATH", "/app/sql/create_meal_table.sql"), "r"
        ) as fh:
            create_table_script = fh.read()
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript(create_table_script)
            conn.commit()

            logger.info("Meals cleared successfully.")

    except sqlite3.Error as e:
        logger.error("Database error while clearing meals: %s", str(e))
        raise e


def delete_meal(meal_id: int) -> None:
    """
    Marks a meal as deleted in the database by setting its 'deleted' flag to TRUE.

    This function performs a soft delete on a meal, ensuring it is not physically removed
    from the database but is instead marked as deleted. If the meal is already deleted
    or does not exist, appropriate errors are raised.

    Args:
        meal_id (int): The ID of the meal to delete.

    Raises:
        ValueError: If the meal with the given ID does not exist or is already marked as deleted.
        sqlite3.Error: If a database error occurs during the operation.

    Logs:
        - Logs an informational message when a meal is successfully marked as deleted.
        - Logs an error message if a database error occurs.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT deleted FROM meals WHERE id = ?", (meal_id,))
            try:
                deleted = cursor.fetchone()[0]
                if deleted:
                    logger.info("Meal with ID %s has already been deleted", meal_id)
                    raise ValueError(f"Meal with ID {meal_id} has been deleted")
            except TypeError:
                logger.info("Meal with ID %s not found", meal_id)
                raise ValueError(f"Meal with ID {meal_id} not found")

            cursor.execute("UPDATE meals SET deleted = TRUE WHERE id = ?", (meal_id,))
            conn.commit()

            logger.info("Meal with ID %s marked as deleted.", meal_id)

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def get_leaderboard(sort_by: str = "wins") -> dict[str, Any]:
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
                "id": row[0],
                "meal": row[1],
                "cuisine": row[2],
                "price": row[3],
                "difficulty": row[4],
                "battles": row[5],
                "wins": row[6],
                "win_pct": round(row[7] * 100, 1),  # Convert to percentage
            }
            leaderboard.append(meal)

        logger.info("Leaderboard retrieved successfully")
        return leaderboard

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def get_meal_by_id(meal_id: int) -> Meal:
    """
    Retrieves a meal from the database by its ID.

    This function fetches the details of a meal by its ID. If the meal is marked
    as deleted or does not exist, appropriate errors are raised.

    Args:
        meal_id (int): The ID of the meal to retrieve.

    Returns:
        Meal: An instance of the `Meal` class representing the retrieved meal.

    Raises:
        ValueError: If the meal is not found or is marked as deleted.
        sqlite3.Error: If a database error occurs during the operation.

    Logs:
        - Logs an informational message if the meal is deleted or not found.
        - Logs an error message if a database error occurs.

    Example:
        meal = get_meal_by_id(1)
        print(meal.price)  # Outputs the price of the retrieved meal.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE id = ?",
                (meal_id,),
            )
            row = cursor.fetchone()

            if row:
                if row[5]:
                    logger.info("Meal with ID %s has been deleted", meal_id)
                    raise ValueError(f"Meal with ID {meal_id} has been deleted")
                return Meal(
                    id=row[0],
                    meal=row[1],
                    cuisine=row[2],
                    price=row[3],
                    difficulty=row[4],
                )
            else:
                logger.info("Meal with ID %s not found", meal_id)
                raise ValueError(f"Meal with ID {meal_id} not found")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def get_meal_by_name(meal_name: str) -> Meal:
    """
    Retrieves a meal from the database by its name.

    This function fetches the details of a meal by its name. If the meal is marked
    as deleted or does not exist, appropriate errors are raised.

    Args:
        meal_name (str): The name of the meal to retrieve.

    Returns:
        Meal: An instance of the `Meal` class representing the retrieved meal.

    Raises:
        ValueError: If the meal is not found or is marked as deleted.
        sqlite3.Error: If a database error occurs during the operation.

    Logs:
        - Logs an informational message if the meal is deleted or not found.
        - Logs an error message if a database error occurs.

    Example:
        meal = get_meal_by_name("Spaghetti")
        print(meal.cuisine)  # Outputs the cuisine type of the retrieved meal.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, meal, cuisine, price, difficulty, deleted FROM meals WHERE meal = ?",
                (meal_name,),
            )
            row = cursor.fetchone()

            if row:
                if row[5]:
                    logger.info("Meal with name %s has been deleted", meal_name)
                    raise ValueError(f"Meal with name {meal_name} has been deleted")
                return Meal(
                    id=row[0],
                    meal=row[1],
                    cuisine=row[2],
                    price=row[3],
                    difficulty=row[4],
                )
            else:
                logger.info("Meal with name %s not found", meal_name)
                raise ValueError(f"Meal with name {meal_name} not found")

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def update_meal_stats(meal_id: int, result: str) -> None:
    """
    Updates the statistics for a meal based on the result of a battle.

    This function increments the number of battles and, if applicable, the number of wins
    for a specific meal in the database. If the meal is marked as deleted or does not exist,
    appropriate errors are raised. The result must be either 'win' or 'loss'.

    Args:
        meal_id (int): The ID of the meal to update.
        result (str): The battle result, either 'win' or 'loss'.

    Raises:
        ValueError: If the meal does not exist, is marked as deleted, or if the result is invalid.
        sqlite3.Error: If a database error occurs during the operation.

    Logs:
        - Logs an informational message when updating a meal's statistics.
        - Logs an error message if a database error occurs.

    Example:
        update_meal_stats(1, "win")
        # Increments both battles and wins for the meal with ID 1.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT deleted FROM meals WHERE id = ?", (meal_id,))
            try:
                deleted = cursor.fetchone()[0]
                if deleted:
                    logger.info("Meal with ID %s has been deleted", meal_id)
                    raise ValueError(f"Meal with ID {meal_id} has been deleted")
            except TypeError:
                logger.info("Meal with ID %s not found", meal_id)
                raise ValueError(f"Meal with ID {meal_id} not found")

            if result == "win":
                cursor.execute(
                    "UPDATE meals SET battles = battles + 1, wins = wins + 1 WHERE id = ?",
                    (meal_id,),
                )
            elif result == "loss":
                cursor.execute(
                    "UPDATE meals SET battles = battles + 1 WHERE id = ?", (meal_id,)
                )
            else:
                raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

            conn.commit()

    except sqlite3.Error as e:
        logger.error("Database error: %s", str(e))
        raise e


def get_all_meals() -> list[dict[str, Any]]:
    """
    Retrieves all meals from the database that are not marked as deleted.

    Returns:
        List[Dict]: A list of meal dictionaries.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, meal, cuisine, price, difficulty FROM meals WHERE deleted = FALSE"
            )
            rows = cursor.fetchall()

        meals = [
            {
                "id": row[0],
                "meal": row[1],
                "cuisine": row[2],
                "price": row[3],
                "difficulty": row[4],
            }
            for row in rows
        ]
        logger.info("All meals retrieved successfully.")
        return meals

    except sqlite3.Error as e:
        logger.error("Database error while retrieving all meals: %s", str(e))
        raise e
