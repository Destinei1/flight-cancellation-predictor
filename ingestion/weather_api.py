# First make sure to import libraries being used

import requests # Helps us call the API
import json  # Helps us read and parse JSON Data

# Instead of leaving my own API Key I wanted to prompt the user for a key

def getWeatherByZipCode(zipCode):

  url = f"https://api.openweathermap.org/data/2.5/weather?zip={zipCode}&appid={API_KEY}&units=imperial"

 #call the API
  response = requests.get(url)

 #convert response to a python object
  jsonWeatherData = json.loads(response.content)

  currTemp = jsonWeatherData["main"]["temp"]
  feelstemp = jsonWeatherData["main"]["feels_like"]
  humidity = jsonWeatherData["main"]["humidity"]
  description = jsonWeatherData["weather"][0]["description"]
  name = jsonWeatherData["name"]

  return {
      "Name of zip": name,
      "Current Temperature": currTemp,
      "Feels like Temp": feelstemp,
      "Description": description
  }
  
  
  getWeatherByZipCode(11430)