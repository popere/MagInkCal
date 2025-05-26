import logging
import requests
import pathlib
import os.path
import json

class WeatherHelper:

    def __init__(self, lat, lon, numDays):
        # Initialise the display
        self.logger = logging.getLogger('maginkcal')
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        if os.path.exists(self.currPath + '/api.key'):
            with open(self.currPath + '/api.key', 'r') as token:
                apiKeyFile = token.read().replace('\n', '')
                self.query = {'q': str(lat) + ',' + str(lon), 'days': numDays, 'key': apiKeyFile, 'lang': 'es'}
                self.logger.info('Weather initialization sucessfully')

    def weather(self):
        if self.query:
            weather = requests.get("https://api.weatherapi.com/v1/forecast.json", params=self.query).json()
            self.logger.info('Weather recovered sucessfully')
            return weather
        else:
            return None
