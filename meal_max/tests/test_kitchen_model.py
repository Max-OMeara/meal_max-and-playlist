
import pytest
from meal_max.models.kitchen_model import create_meal, get_meal_by_id, clear_meals, delete_meal, Meal


@pytest.fixture
def setup_kitchen():
    """Fixture to clear the kitchen and set up meals."""
    clear_meals()
    create_meal("Pizza", "Italian", 10.0, "LOW")
    create_meal("Sushi", "Japanese", 15.0, "MED")


##################################################
# Create and Delete Meal Test Cases
##################################################

def test_create_meal(setup_kitchen):
    """Test creating a new meal."""
    create_meal("Burger", "American", 12.0, "HIGH")
    meal = get_meal_by_id(3)
    assert meal.meal == "Burger"


def test_create_duplicate_meal(setup_kitchen):
    """Test error when creating a duplicate meal."""
    with pytest.raises(ValueError, match="Meal with name 'Pizza' already exists"):
        create_meal("Pizza", "Italian", 10.0, "LOW")


def test_delete_meal(setup_kitchen):
    """Test deleting a meal."""
    delete_meal(1)
    with pytest.raises(ValueError, match="Meal with ID 1 has been deleted"):
        get_meal_by_id(1)


def test_clear_meals():
    """Test clearing all meals."""
    clear_meals()
    with pytest.raises(ValueError, match="Meal with ID 1 not found"):
        get_meal_by_id(1)


##################################################
# Retrieve Meal Test Cases
##################################################

def test_get_meal_by_id(setup_kitchen):
    """Test retrieving a meal by ID."""
    meal = get_meal_by_id(1)
    assert meal.meal == "Pizza"
    assert meal.cuisine == "Italian"
