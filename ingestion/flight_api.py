import requests


def get_flight_data(api_url, params):
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Check if the request was successful
        return response.json()  # Return the JSON data
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


