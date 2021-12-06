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
                self.query = {'lat': lat, 'lon': lon, 'units': units, 'appid': apiKeyFile}
                self.logger.info('weather initializedrecovered sucessfully')

    def weather(self):
        if self.query:
            weather = requests.get("https://api.openweathermap.org/data/2.5/onecall", params=self.query).json()
            return weather
        else:
            return None
