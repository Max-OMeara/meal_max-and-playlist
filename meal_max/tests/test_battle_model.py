import os
import sqlite3
import pytest
from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal
from meal_max.utils.sql_utils import get_db_connection


@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    """Ensure the meals table exists before running tests."""
    create_table_script = """
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY,
        meal TEXT NOT NULL,
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


@pytest.fixture
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()


@pytest.fixture
def sample_meal1():
    """Fixture to provide a sample meal."""
    return Meal(id=1, meal="Pizza", cuisine="Italian", price=10.0, difficulty="LOW")


@pytest.fixture
def sample_meal2():
    """Fixture to provide another sample meal."""
    return Meal(id=2, meal="Sushi", cuisine="Japanese", price=15.0, difficulty="MED")

@pytest.fixture(scope="function")
def populate_database_with_meals(setup_test_database):
    """Insert sample meals into the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript("""
            INSERT INTO meals (id, meal, cuisine, price, difficulty)
            VALUES
                (1, 'Pizza', 'Italian', 10.0, 'LOW'),
                (2, 'Sushi', 'Japanese', 15.0, 'MED');
        """)
        conn.commit()



##################################################
# Combatant Management Test Cases
##################################################

def test_prep_combatant(battle_model, sample_meal1):
    """Test adding a combatant to the list."""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.get_combatants()) == 1


def test_prep_duplicate_combatants(battle_model, sample_meal1):
    """Test error when adding more than two combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal1)  # Adding the same combatant again
    with pytest.raises(ValueError, match="Combatant list is full"):
        battle_model.prep_combatant(sample_meal1)


def test_clear_combatants(battle_model, sample_meal1):
    """Test clearing the combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.clear_combatants()
    assert len(battle_model.get_combatants()) == 0


##################################################
# Battle Test Cases
##################################################

def test_battle(battle_model, sample_meal1, sample_meal2, populate_database_with_meals):
    """Test conducting a battle."""
    battle_model.prep_combatant(sample_meal1)  # Use the in-memory object
    battle_model.prep_combatant(sample_meal2)  # Use the in-memory object
    winner = battle_model.battle()

    assert winner in ["Pizza", "Sushi"]





def test_battle_with_insufficient_combatants(battle_model, sample_meal1):
    """Test error when trying to battle with fewer than two combatants."""
    battle_model.prep_combatant(sample_meal1)
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()
