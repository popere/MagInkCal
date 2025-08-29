#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script essentially generates a HTML file of the calendar I wish to display. It then fires up a headless Chrome
instance, sized to the resolution of the eInk display and takes a screenshot. This screenshot will then be processed
to extract the grayscale and red portions, which are then sent to the eInk display for updating.

This might sound like a convoluted way to generate the calendar, but I'm doing so mainly because (i) it's easier to
format the calendar exactly the way I want it using HTML/CSS, and (ii) I can better delink the generation of the
calendar and refreshing of the eInk display. In the future, I might choose to generate the calendar on a separate
RPi device, while using a ESP32 or PiZero purely to just retrieve the image from a file host and update the screen.
"""
import subprocess
from time import sleep
from datetime import datetime, timedelta
from string import Template
from PIL import Image
import logging
import pathlib

class RenderHelper:

    def __init__(self, width, height, angle):
        self.logger = logging.getLogger('maginkcal')
        self.currPath = str(pathlib.Path(__file__).parent.absolute())
        self.htmlFile = self.currPath + '/calendar.html'
        self.imageWidth = width
        self.imageHeight = height
        self.rotateAngle = angle

    def get_screenshot(self):
        output_file = self.currPath + '/calendar.png'

        # Usamos wkhtmltoimage para renderizar el HTML a PNG
        try:
            cmd = [
                "wkhtmltoimage",
                "--enable-local-file-access",
                "--enable-javascript",
                "--no-stop-slow-scripts",
                "--javascript-delay", "6000",    # ajusta si hace falta
                "--window-status", "ready",      # espera a window.status = 'ready'
                "--disable-smart-width",
                "--debug-javascript",
                "--width", str(self.imageWidth),
                "--height", str(self.imageHeight),
                "--crop-w", str(self.imageWidth),
                "--crop-h", str(self.imageHeight),
                self.htmlFile,
                output_file
            ]
            subprocess.run(cmd, check=True, timeout=60)  # usa timeout de Python
            self.logger.info(f'Screenshot captured and saved to {output_file}')
        except subprocess.TimeoutExpired:
            self.logger.error('wkhtmltoimage timed out')
            raise
        except subprocess.CalledProcessError as e:
            self.logger.error(f'Error running wkhtmltoimage: {e}')
            raise

        # Procesamos la imagen igual que antes
        redimg = Image.open(output_file)
        rpixels = redimg.load()
        blackimg = Image.open(output_file)
        bpixels = blackimg.load()

        for i in range(redimg.size[0]):
            for j in range(redimg.size[1]):
                if rpixels[i, j][0] <= rpixels[i, j][1] and rpixels[i, j][0] <= rpixels[i, j][2]:
                    rpixels[i, j] = (255, 255, 255)
                elif bpixels[i, j][0] > bpixels[i, j][1] and bpixels[i, j][0] > bpixels[i, j][2]:
                    bpixels[i, j] = (255, 255, 255)

        redimg = redimg.rotate(self.rotateAngle, expand=True)
        blackimg = blackimg.rotate(self.rotateAngle, expand=True)

        self.logger.info('Image colours processed. Extracted grayscale and red images.')

        return blackimg, redimg

    def get_day_in_cal(self, startDate, eventDate):
        delta = eventDate - startDate
        return delta.days

    def get_short_time(self, datetimeObj, is24hour=False):
        datetime_str = ''
        if is24hour:
            datetime_str = '{}:{:02d}'.format(datetimeObj.hour, datetimeObj.minute)
        else:
            if datetimeObj.minute > 0:
                datetime_str = '.{:02d}'.format(datetimeObj.minute)

            if datetimeObj.hour == 0:
                datetime_str = '12{}am'.format(datetime_str)
            elif datetimeObj.hour == 12:
                datetime_str = '12{}pm'.format(datetime_str)
            elif datetimeObj.hour > 12:
                datetime_str = '{}{}pm'.format(str(datetimeObj.hour % 12), datetime_str)
            else:
                datetime_str = '{}{}am'.format(str(datetimeObj.hour), datetime_str)
        return datetime_str
    
    


    def process_inputs(self, calDict):
        # calDict = {'events': eventList, 'calStartDate': calStartDate, 'today': currDate, 'lastRefresh': currDatetime, 'batteryLevel': batteryLevel, 'weather' weather}
        # first setup list to represent the 5 weeks in our calendar
        calList = []
        for i in range(6*7):
            calList.append([])

        # retrieve calendar configuration
        maxEventsPerDay = calDict['maxEventsPerDay']
        batteryDisplayMode = calDict['batteryDisplayMode']
        dayOfWeekText = calDict['dayOfWeekText']
        weekStartDay = calDict['weekStartDay']
        is24hour = calDict['is24hour']
        monthsText = calDict['monthsText']

        # for each item in the eventList, add them to the relevant day in our calendar list
        for event in calDict['events']:
            idx = self.get_day_in_cal(calDict['calStartDate'], event['startDatetime'].date())
            if idx >= 0:
                calList[idx].append(event)
            if event['isMultiday']:
                idx = self.get_day_in_cal(calDict['calStartDate'], event['endDatetime'].date())
                if idx < len(calList):
                    calList[idx].append(event)

        # Read html template
        with open(self.currPath + '/calendar_template.html', 'r') as file:
            calendar_template = file.read()

        # Insert month header
        month_name = monthsText[calDict['today'].month - 1]

        # Insert battery icon
        # batteryDisplayMode - 0: do not show / 1: always show / 2: show when battery is low
        battLevel = calDict['batteryLevel']

        if batteryDisplayMode == 0:
            battText = 'batteryHide'
        elif batteryDisplayMode == 1:
            if battLevel >= 80:
                battText = 'battery80'
            elif battLevel >= 60:
                battText = 'battery60'
            elif battLevel >= 40:
                battText = 'battery40'
            elif battLevel >= 20:
                battText = 'battery20'
            else:
                battText = 'battery0'

        elif batteryDisplayMode == 2 and battLevel < 20.0:
            battText = 'battery0'
        elif batteryDisplayMode == 2 and battLevel >= 20.0:
            battText = 'batteryHide'

        # Populate weather
        weatherText = ''
        if (calDict.get('weathers') is not None):
          weathers = calDict['weathers']
          for i in range(len(weathers)):
            w = weathers[i]
            weather = weathers[i]['weather']
            weatherText += '<div class="weather_container">\n'
            weatherText += '<div><div class="city">' + w['city'] + '</div><div class="now align-items-center">' + str(round(weather['current']['temp_c'])) + '°C</div></div>\n'
            weatherText += '<div class="weather_days align-items-center">'
            for j in range(len(w['daysWeather'])): 
              weatherText += '<div class="weather_day text-center">\n'
              if (i == 0 ):
                weatherText += '<p class="weather_day_name">' + w['daysWeather'][j] + '</p>\n'
              weatherText += '<img class="icon" src="https:' + weather['forecast']['forecastday'][j]['day']['condition']['icon'] + '"></img>\n'
              weatherText += '<div>' + str(round(weather['forecast']['forecastday'][j]['day']['maxtemp_c'])) + '°C / ' + str(round(weather['forecast']['forecastday'][j]['day']['mintemp_c'])) + '°C </div>\n'
              if (('maxwind_kph' in weather['forecast']['forecastday'][j]['day']) and weather['forecast']['forecastday'][j]['day']['maxwind_kph'] != 0):
                weatherText += '<div>🍃 ' + str(round(weather['forecast']['forecastday'][j]['day']['maxwind_kph'])) + 'km/h</div>\n'
              if ((weather['forecast']['forecastday'][j]['day']['daily_will_it_snow'] == 1) and weather['forecast']['forecastday'][j]['day']['totalsnow_cm'] != 0 and (weather['forecast']['forecastday'][j]['day']['daily_will_it_rain'] == 1) and weather['forecast']['forecastday'][j]['day']['totalprecip_mm'] != 0):
                weatherText += '<div class="snow">💧/❄️ ' + str(round(weather['forecast']['forecastday'][j]['day']['totalprecip_mm'])) + ' mm / ' + str(round(weather['forecast']['forecastday'][j]['day']['totalsnow_cm'])) + 'cm</div>\n'
              elif ((weather['forecast']['forecastday'][j]['day']['daily_will_it_snow'] == 1) and weather['forecast']['forecastday'][j]['day']['totalsnow_cm'] != 0):
                weatherText += '<div>❄️ ' + str(round(weather['forecast']['forecastday'][j]['day']['totalsnow_cm'])) + 'mm</div>\n'
              elif ((weather['forecast']['forecastday'][j]['day']['daily_will_it_rain'] == 1) and weather['forecast']['forecastday'][j]['day']['totalprecip_mm'] != 0):
                weatherText += '<div>💧 ' + str(round(weather['forecast']['forecastday'][j]['day']['totalprecip_mm'])) + 'mm</div>\n'
              else:
                weatherText += '<div class="no_rain"></div>\n'
              match j:
                case 0:
                  weatherText += '<div class="rain-wrapper">'
                  weatherText += '<div class="rain-chart" id="rainToday-' + str(i) + '"></div>'
                  weatherText += '</div>'
                  weatherText += '<div class="x-axis" id="xToday-' + str(i) + '"></div>'
                case 1:
                  weatherText += '<div class="rain-wrapper">'
                  weatherText += '<div class="rain-chart" id="rainTomorrow-' + str(i) + '"></div>'
                  weatherText += '</div>'
                  weatherText += '<div class="x-axis" id="xTomorrow-' + str(i) + '"></div>'
                case 2:
                  weatherText += '<div class="rain-wrapper">'
                  weatherText += '<div class="rain-chart" id="rainAfter-' + str(i) + '"></div>'
                  weatherText += '</div>'
                  weatherText += '<div class="x-axis" id="xAfter-' + str(i) + '"></div>'
              weatherText += '</div>\n'
            weatherText += '</div>\n'
            weatherText += '</div>\n'

        # Populate the day of week row
        cal_days_of_week = ''
        for i in range(0, 7):
            cal_days_of_week += '<li class="font-weight-bold text-uppercase">' + dayOfWeekText[
                (i + weekStartDay) % 7] + "</li>\n"

        # Populate the date and events
        cal_events_text = '<ol class="days list-unstyled">\n'
        for i in range(len(calList)):
           
            currDate = calDict['calStartDate'] + timedelta(days=i)
            dayOfMonth = currDate.day
            if currDate == calDict['today']:
                cal_events_text += '<li><div class="datecircle">' + str(dayOfMonth) + '</div>\n'
            elif currDate.month != calDict['today'].month:
                cal_events_text += '<li><div class="date text-muted">' + str(dayOfMonth) + '</div>\n'
            else:
                cal_events_text += '<li><div class="date">' + str(dayOfMonth) + '</div>\n'

            for j in range(min(len(calList[i]), maxEventsPerDay)):
                event = calList[i][j]
                event['summary'] = event['summary'].replace('Pádel', '🎾').replace('Padel', '🎾').replace('padel', '🎾').replace('pádel', '🎾')
                cal_events_text += '<div class="event'
                if event['isUpdated']:
                    cal_events_text += ' text-danger'
                elif currDate.month != calDict['today'].month:
                    cal_events_text += ' text-muted'
                if event['isMultiday']:
                    if event['startDatetime'].date() == currDate:
                        cal_events_text += '">►' + event['summary']
                    else:
                        # calHtmlList.append(' text-multiday">')
                        cal_events_text += '">◄' + event['summary']
                elif event['allday'] and (' - Cumpleaños' in event['summary']):
                    cal_events_text += '"> 🎁 ' + event['summary'].replace(' - Cumpleaños', '')
                elif event['allday'] and (('Guardia' in event['summary']) or ('Pase de planta' in event['summary']) or ('Tarde' in event['summary'])):
                    cal_events_text += '"> 🏥 ' + event['summary'].replace('Pase de planta ', '').replace('Residente', 'Resi')
                elif event['allday'] and ('Vacaciones' in event['summary']):
                    cal_events_text += '"> 🏖️ ' + event['summary'].replace('Vacaciones ', 'Vacas')
                elif event['allday']:
                    cal_events_text += '"> - ' + event['summary']
                else:
                    cal_events_text += '"><div> - ' + self.get_short_time(event['startDatetime'], is24hour) + ' ' + event['summary'] + '</div>'
                cal_events_text += '</div>\n'
            if len(calList[i]) > maxEventsPerDay:
                cal_events_text += '<div class="event text-muted">' + str(len(calList[i]) - maxEventsPerDay) + ' more'

            cal_events_text += '</li>\n'
            if (((i+1) % 7) == 0 and i != 1) :
                cal_events_text += '</ol>\n<ol class="days list-unstyled">\n'
        cal_events_text += '</ol>\n'

        def build_rain_arrays(weathers):
            zero_list = ["0.00"] * 24
            zero = ", ".join(zero_list)
            if not weathers or len(weathers) == 0:
                return '[' + zero + ']', '[' + zero + ']', '[' + zero + ']'
            try:
                mm_in_days = [[], [], []]
                for w in weathers:
                    if not w or "weather" not in w:
                        self.logger.warning("Invalid weather data structure.")
                        return '[' + zero + ']', '[' + zero + ']', '[' + zero + ']'
                    else:
                        weather = w.get("weather", {}) or {}
                        forecast_days = weather.get("forecast", {}).get("forecastday", []) or []

                        def day_str(idx: int) -> str:
                            if idx >= len(forecast_days):
                                return zero
                            hours = forecast_days[idx].get("hour", []) or []
                            vals = []
                            for h in range(24):
                                v = 0
                                if h < len(hours):
                                    v = hours[h].get("precip_mm", 0) or 0
                                try:
                                    v = float(v)
                                except Exception:
                                    v = 0.0
                                vals.append(f"{v:.2f}")
                            return ", ".join(vals)

                        mm_in_days[0].append('[' + day_str(0) + ']')
                        mm_in_days[1].append('[' + day_str(1) + ']')
                        mm_in_days[2].append('[' + day_str(2) + ']')
                return ", ".join(mm_in_days[0]), ", ".join(mm_in_days[1]), ", ".join(mm_in_days[2])
            except Exception as e:
                self.logger.warning(f"Failed to extract hourly rain data: {e}")
                return '[' + zero + ']', '[' + zero + ']', '[' + zero + ']'

        rainDataToday, rainDataTomorrow, rainDataAfter = build_rain_arrays(calDict.get('weathers'))


        # Append the bottom and write the file
        htmlFile = open(self.currPath + '/calendar.html', "w")
        tmpl = Template(calendar_template)
        html = tmpl.safe_substitute(
            month=month_name,
            battText=battText,
            dayOfWeek=cal_days_of_week,
            events=cal_events_text,
            weather=weatherText,
            rainDataToday=rainDataToday,
            rainDataTomorrow=rainDataTomorrow,
            rainDataAfter=rainDataAfter,
        )

        with open(self.currPath + '/calendar.html', "w") as htmlFile:
            htmlFile.write(html)
            htmlFile.close()

        self.logger.info('HTML generated')

        calBlackImage, calRedImage = self.get_screenshot()

        threshold = 220  # Puedes ajustar este valor (0-255)
        calBlackImage = calBlackImage.convert('L').point(lambda x: 0 if x < threshold else 255, '1')
        calRedImage = calRedImage.convert('L').point(lambda x: 0 if x < threshold else 255, '1')
        calBlackImage.save(self.currPath + '/calendar_black.png')
        calRedImage.save(self.currPath + '/calendar_red.png')

        return calBlackImage, calRedImage
