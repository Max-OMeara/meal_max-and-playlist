import pytest
from meal_max.models.battle_model import BattleModel
from meal_max.models.kitchen_model import Meal


@pytest.fixture
def battle_model():
    """Provides a fresh instance of BattleModel for each test."""
    return BattleModel()


@pytest.fixture
def sample_meal1():
    """Provides a sample Meal object."""
    return Meal(id=1, meal="Spaghetti", price=10.0, cuisine="Italian", difficulty="MED")


@pytest.fixture
def sample_meal2():
    """Provides another sample Meal object."""
    return Meal(id=2, meal="Sushi", price=15.0, cuisine="Japanese", difficulty="HIGH")


def test_prep_combatant_success(battle_model, sample_meal1):
    """Test adding a combatant successfully."""
    battle_model.prep_combatant(sample_meal1)
    assert len(battle_model.get_combatants()) == 1
    assert battle_model.get_combatants()[0] == sample_meal1


def test_prep_combatant_when_full(battle_model, sample_meal1, sample_meal2):
    """Test that adding a third combatant raises an error."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    with pytest.raises(ValueError, match="Combatant list is full"):
        battle_model.prep_combatant(sample_meal1)


def test_battle_success(battle_model, sample_meal1, sample_meal2, mocker):
    """Test a successful battle between two combatants."""
    # Arrange
    battle_model.prep_combatant(sample_meal1)
    battle_model.prep_combatant(sample_meal2)
    mocker.patch("meal_max.models.battle_model.get_random", return_value=0.5)
    mock_update_stats = mocker.patch("meal_max.models.battle_model.update_meal_stats")

    # Act
    winner = battle_model.battle()

    # Assert
    assert winner in [sample_meal1.meal, sample_meal2.meal]
    assert len(battle_model.get_combatants()) == 1
    mock_update_stats.assert_any_call(sample_meal1.id, mocker.ANY)
    mock_update_stats.assert_any_call(sample_meal2.id, mocker.ANY)


def test_battle_insufficient_combatants(battle_model):
    """Test that battle raises an error when there are fewer than two combatants."""
    with pytest.raises(ValueError, match="Two combatants must be prepped"):
        battle_model.battle()


def test_clear_combatants(battle_model, sample_meal1):
    """Test that combatants can be cleared."""
    battle_model.prep_combatant(sample_meal1)
    battle_model.clear_combatants()
    assert len(battle_model.get_combatants()) == 0


def test_get_battle_score(battle_model, sample_meal1):
    """Test calculating the battle score for a combatant."""
    score = battle_model.get_battle_score(sample_meal1)
    expected_score = (sample_meal1.price * len(sample_meal1.cuisine)) - {
        "HIGH": 1,
        "MED": 2,
        "LOW": 3,
    }[sample_meal1.difficulty]
    assert score == expected_score
