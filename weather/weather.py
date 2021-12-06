import logging
import requests
import pathlib
import os.path
import json

class WeatherHelper:

    def __init__(self, lat, lon, units):
        # Initialise the display
        self.logger = logging.getLogger('maginkcal')
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        if os.path.exists(self.currPath + '/api.key'):
            with open(self.currPath + '/api.key', 'r') as token:
                apiKeyFile = token.read().replace('\n', '')
        query = {'lat': lat, 'lon': lon, 'units': units, 'appid': apiKeyFile}
        self.logger.warn(json.dumps(query))
        self.weather = requests.get("https://api.openweathermap.org/data/2.5/onecall", params=query).json()
        self.logger.warn('weather: ' + json.dumps(self.weather))

    def weather(self):
      return self.weather
