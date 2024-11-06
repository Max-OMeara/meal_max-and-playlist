import pytest
from unittest.mock import Mock

from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal

######################################################
#
#    Fixtures
#
######################################################

@pytest.fixture()
def battle_model():
    """Fixture to provide a new instance of BattleModel for each test."""
    return BattleModel()

@pytest.fixture
def sample_meal1():
    return Meal(id=1, meal='Meal 1', cuisine='CuisineA', price=10.0, difficulty='LOW')

@pytest.fixture
def sample_meal2():
    return Meal(id=2, meal='Meal 2', cuisine='CuisineB', price=15.0, difficulty='MED')

@pytest.fixture
def sample_meal3():
    return Meal(id=3, meal='Meal 3', cuisine='CuisineC', price=20.0, difficulty='HIGH')

######################################################
#
#    Test Cases
#
######################################################

def test_prep_combatant(battle_model, sample_meal1):
    """Test adding a combatant to the battle model."""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.combatants) == 1
    assert battle_model.combatants[0].meal == 'Meal 1'

def test_prep_combatant_full(battle_model, sample_meal1, sample_meal2, sample_meal3):
    """Test that adding more than two combatants raises an error."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    with pytest.raises(ValueError, match="Combatant list is full, cannot add more combatants."):
        battle_model.prep_combatant(sample_meal3)

def test_get_combatants(battle_model, sample_meal1, sample_meal2):
    """Test retrieving the current list of combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    combatants = battle_model.get_combatants()
    assert len(combatants) == 2
    assert combatants[0].meal == 'Meal 1'
    assert combatants[1].meal == 'Meal 2'

def test_get_battle_score(battle_model, sample_meal1):
    """Test calculating the battle score for a combatant."""
    score = battle_model.get_battle_score(sample_meal1)
    difficulty_modifier = {"HIGH": 1, "MED": 2, "LOW": 3}
    expected_score = (sample_meal1.price * len(sample_meal1.cuisine)) - difficulty_modifier[sample_meal1.difficulty]
    assert score == expected_score, f"Expected score {expected_score}, got {score}"

def test_battle(battle_model, sample_meal1, sample_meal2, mocker):
    """Test conducting a battle between two combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)

    # Mock get_random to return a fixed value
    mocker.patch('meal_max.battle.models.battle_model.get_random', return_value=0.01)
    # Mock update_meal_stats to avoid actual database calls
    mock_update_meal_stats = mocker.patch('meal_max.battle.models.battle_model.update_meal_stats')

    winner_name = battle_model.battle()

    # Based on the mock and sample data, determine expected winner
    score_1 = battle_model.get_battle_score(sample_meal1)
    score_2 = battle_model.get_battle_score(sample_meal2)
    delta = abs(score_1 - score_2) / 100

    # Determine expected winner based on delta and random number
    if score_1 > score_2:
        expected_winner = sample_meal1.meal if delta > 0.01 else sample_meal2.meal
    else:
        expected_winner = sample_meal2.meal if delta > 0.01 else sample_meal1.meal

    assert winner_name == expected_winner, f"Expected winner {expected_winner}, got {winner_name}"
    assert len(battle_model.combatants) == 1, "One combatant should remain after the battle"
    assert battle_model.combatants[0].meal == winner_name, "Remaining combatant should be the winner"

    # Assert that update_meal_stats was called correctly
    winner_id = sample_meal1.id if sample_meal1.meal == winner_name else sample_meal2.id
    loser_id = sample_meal2.id if sample_meal1.meal == winner_name else sample_meal1.id
    mock_update_meal_stats.assert_any_call(winner_id, 'win')
    mock_update_meal_stats.assert_any_call(loser_id, 'loss')
    assert mock_update_meal_stats.call_count == 2, "update_meal_stats should be called twice"

def test_battle_not_enough_combatants(battle_model, sample_meal1):
    """Test that battle raises an error if there are fewer than two combatants."""
    battle_model.prep_combatant(sample_meal1)
    with pytest.raises(ValueError, match="Two combatants must be prepped for a battle."):
        battle_model.battle()

def test_clear_combatants(battle_model, sample_meal1, sample_meal2):
    """Test clearing the list of combatants."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    assert len(battle_model.combatants) == 2

    battle_model.clear_combatants()
    assert len(battle_model.combatants) == 0, "Combatants list should be empty after clearing"