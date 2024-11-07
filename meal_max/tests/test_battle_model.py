import pytest
from unittest.mock import patch, Mock

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal, update_meal_stats
from meal_max.utils.sql_utils import get_db_connection
from meal_max.models.kitchen_model import get_leaderboard


@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    """Ensure the meals table is fresh before running tests."""
    create_table_script = """
    DROP TABLE IF EXISTS meals;
    CREATE TABLE meals (
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


@pytest.fixture(scope="function")
def populate_database_with_meals(setup_test_database):
    """Insert sample meals into the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.executescript("""
            DELETE FROM meals;
            INSERT INTO meals (id, meal, cuisine, price, difficulty)
            VALUES
                (1, 'Pizza', 'Italian', 10.0, 'LOW'),
                (2, 'Sushi', 'Japanese', 15.0, 'MED');
        """)
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


@pytest.fixture
def sample_meal3():
    """Fixture to provide a third sample meal."""
    return Meal(id=3, meal="Burger", cuisine="American", price=12.0, difficulty="HIGH")


##################################################
# Combatant Management Test Cases
##################################################

def test_prep_combatant(battle_model, sample_meal1):
    """Test adding a combatant to the list."""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.get_combatants()) == 1
    assert battle_model.get_combatants()[0] == sample_meal1

def test_prep_combatant_invalid_type(battle_model):
    """Test adding an invalid type as a combatant."""
    with pytest.raises(AttributeError):
        battle_model.prep_combatant("Not a Meal object")

def test_prep_combatant_full_list(battle_model, sample_meal1, sample_meal2, sample_meal3):
    """Test error when adding more than two combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(sample_meal3)

def test_get_combatants(battle_model, sample_meal1, sample_meal2):
    """Test retrieving the current list of combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    combatants = battle_model.get_combatants()
    assert combatants == [sample_meal1, sample_meal2]

def test_clear_combatants(battle_model, sample_meal1, sample_meal2):
    """Test clearing the combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    battle_model.clear_combatants()
    assert len(battle_model.get_combatants()) == 0

def test_clear_combatants_empty_list(battle_model):
    """Test clearing combatants when the list is already empty."""
    battle_model.clear_combatants()
    assert len(battle_model.get_combatants()) == 0

##################################################
# Battle Test Cases
##################################################

@patch('meal_max.models.battle_model.get_random')
@patch('meal_max.models.battle_model.update_meal_stats')
@patch('meal_max.models.battle_model.logger')
def test_battle(mock_logger, mock_update_meal_stats, mock_get_random, battle_model, sample_meal1, sample_meal2):
    """Test conducting a battle with proper winner determination."""
    # Prepare combatants
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    # Mock get_random to return a specific value
    mock_get_random.return_value = 0.15  # Random number for testing

    # Mock battle scores for combatants
    score_1 = 80.0
    score_2 = 70.0
    with patch.object(BattleModel, 'get_battle_score', side_effect=[score_1, score_2]):
        winner = battle_model.battle()

    # Calculate expected results
    delta = abs(score_1 - score_2) / 100  # Calculate delta
    expected_winner = sample_meal1 if delta > 0.15 else sample_meal2
    expected_loser = sample_meal2 if expected_winner == sample_meal1 else sample_meal1

    # Assert the correct winner is determined
    assert winner == expected_winner.meal, (
        f"Expected winner {expected_winner.meal}, but got {winner}"
    )

    # Assert loser is removed from combatants
    remaining_combatants = battle_model.get_combatants()
    assert remaining_combatants == [expected_winner], (
        f"Loser should be removed from combatants. Remaining combatants: {remaining_combatants}"
    )

    # Verify update_meal_stats was called correctly
    mock_update_meal_stats.assert_any_call(expected_winner.id, 'win')
    mock_update_meal_stats.assert_any_call(expected_loser.id, 'loss')
    assert mock_update_meal_stats.call_count == 2

@patch('meal_max.models.battle_model.get_random')
@patch('meal_max.models.battle_model.update_meal_stats')
def test_battle_random_outcome(mock_update_meal_stats, mock_get_random, battle_model, sample_meal1, sample_meal2):
    """Test conducting a battle where the random number affects the outcome."""
    # Prepare combatants
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    # Mock get_random to return a fixed value
    mock_get_random.return_value = 0.15  # Higher value for testing

    # Mock get_battle_score to control scores
    with patch.object(BattleModel, 'get_battle_score', side_effect=[70.0, 80.0]):
        winner = battle_model.battle()

    # Since delta is (80 - 70)/100 = 0.1, which is less than 0.15
    # The winner should be sample_meal2 ('Sushi')
    assert winner == sample_meal2.meal
    assert battle_model.get_combatants() == [sample_meal2], "Loser should be removed from combatants"



    # # Verify that update_meal_stats was called correctly
    # mock_update_meal_stats.assert_any_call(sample_meal2.id, 'win')
    # mock_update_meal_stats.assert_any_call(sample_meal1.id, 'loss')
    # assert mock_update_meal_stats.call_count == 2

def test_battle_with_insufficient_combatants(battle_model, sample_meal1):
    """Test error when trying to battle with fewer than two combatants."""
    battle_model.prep_combatant(sample_meal1)
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

def test_battle_with_no_combatants(battle_model):
    """Test error when trying to battle with no combatants."""
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

##################################################
# get_battle_score Test Cases
##################################################

def test_get_battle_score_low_difficulty(battle_model, sample_meal1):
    """Test battle score calculation for LOW difficulty."""
    score = battle_model.get_battle_score(sample_meal1)
    expected_score = (sample_meal1.price * len(sample_meal1.cuisine)) - 3  # LOW difficulty modifier is 3
    assert score == expected_score

def test_get_battle_score_med_difficulty(battle_model, sample_meal2):
    """Test battle score calculation for MED difficulty."""
    score = battle_model.get_battle_score(sample_meal2)
    expected_score = (sample_meal2.price * len(sample_meal2.cuisine)) - 2  # MED difficulty modifier is 2
    assert score == expected_score

def test_get_battle_score_high_difficulty(battle_model, sample_meal3):
    """Test battle score calculation for HIGH difficulty."""
    score = battle_model.get_battle_score(sample_meal3)
    expected_score = (sample_meal3.price * len(sample_meal3.cuisine)) - 1  # HIGH difficulty modifier is 1
    assert score == expected_score

def test_get_battle_score_invalid_difficulty(battle_model):
    """Test battle score calculation with invalid difficulty."""
    with pytest.raises(ValueError, match="Difficulty must be 'LOW', 'MED', or 'HIGH'."):
        invalid_meal = Meal(id=4, meal="Invalid Meal", cuisine="Test", price=10.0, difficulty="INVALID")
        battle_model.get_battle_score(invalid_meal)


##################################################
# Edge Case Test Cases
##################################################

def test_prep_combatant_same_meal(battle_model, sample_meal1):
    """Test adding the same meal object as both combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal1)  # Adding the same meal again
    assert len(battle_model.get_combatants()) == 2
    assert battle_model.get_combatants()[0] == battle_model.get_combatants()[1]

def test_battle_same_meal(battle_model, sample_meal1, populate_database_with_meals):
    """Test conducting a battle where both combatants are the same meal."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal1)
    winner = battle_model.battle()
    assert winner == sample_meal1.meal
    assert len(battle_model.get_combatants()) == 1


@patch('meal_max.models.battle_model.get_random')
def test_battle_zero_delta(mock_get_random, battle_model, sample_meal1, sample_meal2, populate_database_with_meals):
    """Test battle where delta between scores is zero."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    # Set the mock return value
    mock_get_random.return_value = 0.1

    # Mock get_battle_score to return the same score for both
    with patch.object(BattleModel, 'get_battle_score', return_value=100.0):
        winner = battle_model.battle()

    # Since delta is zero, winner should be determined by random number
    assert winner in [sample_meal1.meal, sample_meal2.meal]
    assert len(battle_model.get_combatants()) == 1




def test_get_combatants_after_battle(battle_model, sample_meal1, sample_meal2, populate_database_with_meals):
    """Test that the losing combatant is removed after the battle."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    # Mock get_battle_score to control scores
    with patch.object(BattleModel, 'get_battle_score', side_effect=[100.0, 90.0]):
        with patch('meal_max.models.battle_model.get_random', return_value=0.05):
            battle_model.battle()

    combatants = battle_model.get_combatants()
    assert len(combatants) == 1
    assert combatants[0] == sample_meal1

@patch('meal_max.models.battle_model.update_meal_stats')
def test_update_meal_stats_called(mock_update_stats, battle_model, sample_meal1, sample_meal2):
    """Test that update_meal_stats is called correctly."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    with patch.object(BattleModel, 'get_battle_score', side_effect=[100.0, 80.0]):
        with patch('meal_max.models.battle_model.get_random', return_value=0.1):
            battle_model.battle()

    mock_update_stats.assert_any_call(sample_meal1.id, 'win')
    mock_update_stats.assert_any_call(sample_meal2.id, 'loss')
    assert mock_update_stats.call_count == 2

def test_battle_exception_during_update_stats(battle_model, sample_meal1, sample_meal2):
    """Test handling of exceptions during update_meal_stats."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    with patch('meal_max.models.battle_model.update_meal_stats', side_effect=Exception("Database Error")):
        with patch.object(BattleModel, 'get_battle_score', side_effect=[100.0, 80.0]):
            with pytest.raises(Exception, match="Database Error"):
                battle_model.battle()

##################################################
# Additional Test Cases
##################################################

def test_prep_combatant_after_battle(battle_model, sample_meal1, sample_meal2, sample_meal3, populate_database_with_meals):
    """Test adding a new combatant after a battle has removed one."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    with patch.object(BattleModel, 'get_battle_score', side_effect=[100.0, 80.0]):
        with patch('meal_max.models.battle_model.get_random', return_value=0.1):
            battle_model.battle()

    # Now only one combatant remains, we should be able to add another
    battle_model.prep_combatant(sample_meal3)
    assert len(battle_model.get_combatants()) == 2



def test_get_battle_score_zero_price(battle_model):
    """Test get_battle_score with zero price."""
    zero_price_meal = Meal(id=5, meal="Free Meal", cuisine="None", price=0.0, difficulty="LOW")
    score = battle_model.get_battle_score(zero_price_meal)
    expected_score = (0.0 * len(zero_price_meal.cuisine)) - 3  # LOW difficulty modifier is 3
    assert score == expected_score

def test_get_battle_score_empty_cuisine(battle_model):
    """Test get_battle_score with empty cuisine."""
    empty_cuisine_meal = Meal(id=6, meal="Mystery Meal", cuisine="", price=10.0, difficulty="LOW")
    score = battle_model.get_battle_score(empty_cuisine_meal)
    expected_score = (10.0 * 0) - 3  # Cuisine length is 0
    assert score == expected_score

def test_leaderboard_no_battles(populate_database_with_meals):
    """Test leaderboard when no meals have battles."""
    leaderboard = get_leaderboard()
    assert leaderboard == [], "Leaderboard should be empty if no battles have occurred."


