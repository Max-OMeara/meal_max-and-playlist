import pytest
import requests
from meal_max.utils.random_utils import get_random
from unittest.mock import patch

RANDOM_NUMBER=0.123

@pytest.fixture
def mock_random_org(mocker):
    # Patch the requests.get call
    mock_response = mocker.Mock()
    # We are giving that object a text attribute
    mock_response.text = f"{RANDOM_NUMBER}\n"
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response

@patch("meal_max.utils.random_utils.requests.get")
def test_get_random(mock_get):
    """Test retrieving a random number from random.org."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = "3"
    random_number = get_random()  # Remove argument if unnecessary
    assert random_number == 3






def test_get_random_request_failure(mocker):
    """Simulate a request failure."""
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to random.org failed: Connection error"):
        get_random()

def test_get_random_timeout(mocker):
    """Simulate a timeout."""
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to random.org timed out."):
        get_random()

def test_get_random_invalid_response(mock_random_org):
    """Simulate an invalid response (non-digit)."""
    mock_random_org.text = "invalid_response\n"

    with pytest.raises(ValueError, match="Invalid response from random.org: invalid_response"):
        get_random()