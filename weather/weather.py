import logging
import requests
import pathlib
import os.path



class WeatherHelper:

    def __init__(self, lat, long, units):
        # Initialise the display
        self.logger = logging.getLogger('maginkcal')
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        if os.path.exists(self.currPath + '/api.key'):
            with open(self.currPath + '/api.key', 'rb') as token:
                apiKeyFile = token.read().rstrip()
        self.logger.warn('apiKeyFile: ' + apiKeyFile)
        query = {'lat': lat, 'long': long, 'units': units, 'api': apiKeyFile}
        self.weather = requests.get("https://api.openweathermap.org/data/2.5/onecall", params=query).json()
        self.logger.warn('apiKeyFile: ' + apiKeyFile)

    def weather(self):
      return self.weather
