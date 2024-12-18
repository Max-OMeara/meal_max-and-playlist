#!/bin/bash

export $(cat .env | xargs) # Load environment variables

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

##################################################
#
# Health Checks
#
##################################################

# Check if the service is healthy
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

# Check the database connection
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

##################################################
#
# Meal Management
#
##################################################

# Function to clear all meals
clear_meals() {
  echo "Clearing all meals..."
  curl -s -X POST "$BASE_URL/clear-meals" | grep -q '"status": "success"'
}

# Function to create a meal
create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Creating meal: $meal ($cuisine, $price, $difficulty)..."
  curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" \
    -d "{\"meal\":\"$meal\", \"cuisine\":\"$cuisine\", \"price\":$price, \"difficulty\":\"$difficulty\"}" | grep -q '"status": "success"'
  
  if [ $? -eq 0 ]; then
    echo "Meal created successfully."
  else
    echo "Failed to create meal."
    exit 1
  fi
}

# Function to update meal stats
# Newly added
update_meal_stats() {
  meal_id=$1
  result=$2

  echo "Updating meal stats for meal ID ($meal_id) with result ($result)..."
  response=$(curl -s -X PUT "$BASE_URL/update-meal-stats/$meal_id" -H "Content-Type: application/json" \
    -d "{\"result\": \"$result\"}")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal stats updated successfully for ID ($meal_id)."
  else
    echo "Failed to update meal stats for ID ($meal_id)."
    exit 1
  fi
}

# Function to delete a meal by ID
delete_meal_by_id() {
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully by ID ($meal_id)."
  else
    echo "Failed to delete meal by ID ($meal_id)."
    exit 1
  fi
}

# Function to get a meal by name
get_meal_by_name() {
  meal_name=$1

  echo "Getting meal by name ($meal_name)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-name/$meal_name")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by name ($meal_name)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (Name $meal_name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name ($meal_name)."
    exit 1
  fi
}

# Function to get all meals
get_all_meals() {
  echo "Retrieving all meals..."
  response=$(curl -s -X GET "$BASE_URL/meals")
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

##################################################
#
# Battle Management
#
##################################################

# Function to prepare a meal for battle
prep_combatant() {
  meal_name=$1

  echo "Preparing meal ($meal_name) for battle..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant" -H "Content-Type: application/json" \
    -d "{\"meal\": \"$meal_name\"}")
  
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal prepared for battle successfully."
  else
    echo "Failed to prepare meal for battle."
    exit 1
  fi
}

# Function to clear combatants
# Newly added
clear_combatants() {
  echo "Clearing all combatants..."
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants cleared successfully."
  else
    echo "Failed to clear combatants."
    exit 1
  fi
}

# Function to get combatants
# Newly added
get_combatants() {
  echo "Retrieving combatants..."
  response=$(curl -s -X GET "$BASE_URL/get-combatants")
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

# Function to start a battle
start_battle() {
  echo "Starting a battle..."
  response=$(curl -s -X POST "$BASE_URL/battle")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Battle started successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Battle Result JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to start battle."
    exit 1
  fi
}

# Function to retrieve the leaderboard
get_leaderboard() {
  echo "Retrieving the leaderboard..."
  response=$(curl -s -X GET "$BASE_URL/leaderboard")
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

##################################################
#
# Running the Tests
#
##################################################

# Run health checks
check_health
check_db

# Clear all meals
clear_meals

# Create sample meals
create_meal "Spaghetti" "Italian" 10.0 "MED"
create_meal "Sushi" "Japanese" 15.0 "HIGH"
create_meal "Tacos" "Mexican" 8.0 "LOW"

# Get all meals
get_all_meals

# Prepare meals for battle (using meal names)
prep_combatant "Spaghetti"
prep_combatant "Sushi"

# Retrieve combatants
get_combatants # Newly added

# Start the battle
start_battle

# Get leaderboard
get_leaderboard

# Update meal stats
update_meal_stats 1 "win" # Newly added

# Get meal by name
get_meal_by_name "Spaghetti" # Newly added

# Clear combatants
clear_combatants # Newly added

# Clean up by deleting meals
delete_meal_by_id 1
delete_meal_by_id 2
delete_meal_by_id 3

# Final check
get_all_meals

echo "All smoketests completed successfully."
