#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

###############################################
#
# Health checks
#
###############################################

check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}

###############################################
#
# Kitchen Management
#
###############################################

clear_kitchen() {
  echo "Clearing all meals..."
  curl -s -X DELETE "$BASE_URL/kitchen/clear" | grep -q '"status": "success"'
}

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Creating meal ($meal, $cuisine, $price, $difficulty)..."
  curl -s -X POST "$BASE_URL/kitchen/create" -H "Content-Type: application/json" \
    -d "{\"meal\": \"$meal\", \"cuisine\": \"$cuisine\", \"price\": $price, \"difficulty\": \"$difficulty\"}" | grep -q '"status": "success"'

  if [ $? -eq 0 ]; then
    echo "Meal created successfully."
  else
    echo "Failed to create meal."
    exit 1
  fi
}

get_all_meals() {
  echo "Retrieving all meals..."
  response=$(curl -s -X GET "$BASE_URL/kitchen/get-all")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "All meals retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meals JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve meals."
    exit 1
  fi
}

get_meal_by_id() {
  meal_id=$1

  echo "Retrieving meal by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/kitchen/get/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve meal by ID."
    exit 1
  fi
}

delete_meal_by_id() {
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/kitchen/delete/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully."
  else
    echo "Failed to delete meal by ID."
    exit 1
  fi
}

get_leaderboard() {
  echo "Retrieving meal leaderboard..."
  response=$(curl -s -X GET "$BASE_URL/kitchen/leaderboard")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve leaderboard."
    exit 1
  fi
}

###############################################
#
# Battle Management
#
###############################################

prep_combatant() {
  meal_id=$1

  echo "Preparing meal for battle (ID: $meal_id)..."
  response=$(curl -s -X POST "$BASE_URL/battle/prep" -H "Content-Type: application/json" \
    -d "{\"meal_id\": $meal_id}")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal prepped successfully."
  else
    echo "Failed to prep meal."
    exit 1
  fi
}

start_battle() {
  echo "Starting battle..."
  response=$(curl -s -X POST "$BASE_URL/battle/start")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle completed successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Battle Results JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to start battle."
    exit 1
  fi
}

get_combatants() {
  echo "Retrieving current combatants..."
  response=$(curl -s -X GET "$BASE_URL/battle/combatants")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatants JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve combatants."
    exit 1
  fi
}

clear_combatants() {
  echo "Clearing all combatants..."
  response=$(curl -s -X DELETE "$BASE_URL/battle/clear")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants cleared successfully."
  else
    echo "Failed to clear combatants."
    exit 1
  fi
}

###############################################
#
# Smoke Test Execution
#
###############################################

# Health checks
check_health
check_db

# Kitchen tests
clear_kitchen
create_meal "Pizza" "Italian" 10.0 "LOW"
create_meal "Sushi" "Japanese" 15.0 "MED"
create_meal "Burger" "American" 12.0 "HIGH"
get_all_meals
get_meal_by_id 1
delete_meal_by_id 2
get_leaderboard

# Battle tests
prep_combatant 1
prep_combatant 3
get_combatants
start_battle
get_combatants
clear_combatants

echo "MealMax smoke test completed successfully!"
