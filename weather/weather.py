import logging
import requests

class WeatherHelper:

    def __init__(self, lat, long, units):
        # Initialise the display
        self.logger = logging.getLogger('maginkcal')
        apiKeyFile = open('api.key')
        self.logger.warn('apiKeyFile: ' + apiKeyFile)
        query = {'lat': lat, 'long': long, 'units': units, 'api': apiKeyFile}
        self.weather = requests.get("https://api.openweathermap.org/data/2.5/onecall", params=query).json()
        self.logger.warn('apiKeyFile: ' + apiKeyFile)

    def weather(self):
      return self.weather
