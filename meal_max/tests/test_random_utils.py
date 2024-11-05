import pytest
import requests
from unittest.mock import Mock
from meal_max.meal_max.utils.random_utils import get_random


@pytest.fixture
def mock_random_org(mocker):
    """
    Fixture to mock the response from random.org.

    Mocks the `requests.get` call to return a controlled response for testing.
    Sets the text of the mock response to simulate a valid random number.

    Args:
        mocker (pytest-mock fixture): The mocker fixture for patching.

    Returns:
        Mock: A mocked response object with a preset text attribute.
    """
    mock_response = mocker.Mock()
    mock_response.text = "0.42"  # Mocking a valid float response as text
    mocker.patch("requests.get", return_value=mock_response)
    return mock_response


def test_get_random(mock_random_org):
    """
    Test retrieving a random float from random.org.

    Asserts that the returned result is the mocked random number and checks
    that the correct URL was called with the appropriate timeout.

    Args:
        mock_random_org (Mock): The mock response from random.org.
    """
    result = get_random()

    # Assert that the result matches the mocked random number
    assert result == 0.42, f"Expected random number 0.42, but got {result}"

    # Ensure that the correct URL was called
    requests.get.assert_called_once_with(
        "https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new", timeout=5)


def test_get_random_request_failure(mocker):
    """
    Test handling of request failures.

    Mocks a general request failure when calling random.org and verifies that
    a RuntimeError is raised with an appropriate error message.

    Args:
        mocker (pytest-mock fixture): The mocker fixture for patching.
    """
    mocker.patch("requests.get", side_effect=requests.exceptions.RequestException("Connection error"))

    with pytest.raises(RuntimeError, match="Request to random.org failed: Connection error"):
        get_random()


def test_get_random_timeout(mocker):
    """
    Test handling of timeout errors.

    Simulates a timeout error when calling random.org and asserts that a
    RuntimeError is raised with a relevant timeout message.

    Args:
        mocker (pytest-mock fixture): The mocker fixture for patching.
    """
    mocker.patch("requests.get", side_effect=requests.exceptions.Timeout)

    with pytest.raises(RuntimeError, match="Request to random.org timed out."):
        get_random()


def test_get_random_invalid_response(mock_random_org):
    """
    Test handling of invalid responses from random.org.

    Mocks a response with invalid (non-numeric) content and verifies that a
    ValueError is raised with an appropriate error message.

    Args:
        mock_random_org (Mock): The mock response from random.org with invalid content.
    """
    mock_random_org.text = "invalid_response"  # Mocking an invalid response

    with pytest.raises(ValueError, match="Invalid response from random.org: invalid_response"):
        get_random()
