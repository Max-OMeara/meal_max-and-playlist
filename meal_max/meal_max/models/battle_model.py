import logging
from typing import List
from meal_max.models.kitchen_model import Meal, update_meal_stats
from meal_max.utils.logger import configure_logger
from meal_max.utils.random_utils import get_random

logger = logging.getLogger(__name__)
configure_logger(logger)


class BattleModel:
    """
    A class to manage battles between meal combatants.

    Attributes:
        combatants (List[Meal]): List of meals ready for battle.
    """

    def __init__(self):
        """Initializes the BattleModel with an empty list of combatants."""
        self.combatants: List[Meal] = []

    def battle(self) -> str:
        """
        Conducts a battle between two meal combatants and determines a winner.

        Returns:
            str: The name of the winning meal.

        Raises:
            ValueError: If there are fewer than two combatants.
        """
        logger.info("Two meals enter, one meal leaves!")

        if len(self.combatants) < 2:
            logger.error("Not enough combatants to start a battle.")
            raise ValueError("Two combatants must be prepped for a battle.")

        combatant_1 = self.combatants[0]
        combatant_2 = self.combatants[1]

        logger.info("Battle started between %s and %s", combatant_1.meal, combatant_2.meal)

        score_1 = self.get_battle_score(combatant_1)
        score_2 = self.get_battle_score(combatant_2)

        logger.info("Score for %s: %.3f", combatant_1.meal, score_1)
        logger.info("Score for %s: %.3f", combatant_2.meal, score_2)

        delta = abs(score_1 - score_2) / 100
        logger.info("Delta between scores: %.3f", delta)

        random_number = get_random()
        logger.info("Random number from random.org: %.3f", random_number)

        if delta > random_number:
            winner = combatant_1
            loser = combatant_2
        else:
            winner = combatant_2
            loser = combatant_1

        logger.info("The winner is: %s", winner.meal)

        update_meal_stats(winner.id, 'win')
        update_meal_stats(loser.id, 'loss')

        self.combatants.remove(loser)

        return winner.meal

    def clear_combatants(self) -> None:
        """Clears the list of combatants."""
        logger.info("Clearing the combatants list.")
        self.combatants.clear()

    def get_battle_score(self, combatant: Meal) -> float:
        """
        Calculates the battle score for a combatant based on its attributes.

        Args:
            combatant (Meal): The meal combatant whose score is to be calculated.

        Returns:
            float: The calculated battle score for the combatant.
        """
        difficulty_modifier = {"HIGH": 1, "MED": 2, "LOW": 3}

        logger.info("Calculating battle score for %s: price=%.3f, cuisine=%s, difficulty=%s",
                    combatant.meal, combatant.price, combatant.cuisine, combatant.difficulty)

        score = (combatant.price * len(combatant.cuisine)) - difficulty_modifier[combatant.difficulty]
        logger.info("Battle score for %s: %.3f", combatant.meal, score)

        return score

    def get_combatants(self) -> List[Meal]:
        """
        Retrieves the current list of combatants.

        Returns:
            List[Meal]: The list of current combatants.
        """
        logger.info("Retrieving current list of combatants.")
        return self.combatants

    def prep_combatant(self, combatant_data: Meal) -> None:
        """
        Prepares a meal combatant for battle by adding it to the combatants list.

        Args:
            combatant_data (Meal): The meal combatant to add.

        Raises:
            ValueError: If there are already two combatants prepared.
        """
        if len(self.combatants) >= 2:
            logger.error("Attempted to add combatant '%s' but combatants list is full", combatant_data.meal)
            raise ValueError("Combatant list is full, cannot add more combatants.")

        logger.info("Adding combatant '%s' to combatants list", combatant_data.meal)
        self.combatants.append(combatant_data)
        logger.info("Current combatants list: %s", [combatant.meal for combatant in self.combatants])
