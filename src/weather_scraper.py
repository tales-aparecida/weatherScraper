#!/usr/bin/env python
'''
This file implements a scraper for the page at https://cgesp.org/v3/estacoes-meteorologicas.jsp,
returning its content as a JSON:
{
  "region_name": [
    {
        "timestamp": number,        # epoch based timestamp
        "chuva": number,            # rain (mm)
        "vel_vento": number,        # wind speed (m/s)
        "dir_vento": number,        # wind direction (arc degrees 0-360º)
        "temp": number,             # temperature (ºC)
        "umidadade_rel": number,    # air humidity (%)
        "pressao": number           # air pressure (mbar)
    },
    ...
  ],
  ...
}

Author: Tales Lelo da Aparecida  -  Date: 18/12/2018
        tales dot aparecida at gmail dot com

'''

import datetime
import json
import logging
import time
import tempfile
from http.client import HTTPException

import requests
from bs4 import BeautifulSoup

try:
    from logger import setup_logging
except ModuleNotFoundError:
    from .logger import setup_logging

# Wait between request to avoid overwhelming the network
FETCH_POLITELY = False

# URL to fetch the station list
MAIN_URL = 'https://www.cgesp.org/v3/estacoes-meteorologicas.jsp'

# URL to fetch a station/region measurement table
REGION_URL = 'https://www.saisp.br/geral/processo_cge.jsp?WHICHCHANNEL={}'

# URL used to spoof the referer, allowing us to fetch the measurements table
REFERER_URL = 'https://www.saisp.br'

# Months list, used to convert tha table date to epoch
MONTH_DICT = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI',
              'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']

# Attributes dictionary to translate a table column to our instance attr
LABEL_DICT = {
    'Data': 'timestamp',
    'Chuva(mm)': 'rain',
    'Vel.VT(m/s)': 'wind_speed',
    'Dir.VT(o)': 'wind_direction',
    'Temp(oC)': 'temperature',
    'Umid.Rel.(%)': 'humidity',
    'Pressão(mb)': 'pressure'
}

# Expected bounderies for scraped values
BOUNDS = {
    'timestamp': (0, 10**11),  # Enough seconds to last more than 3000 years
    'humidity': (0, 100),  # from 0 to 100%
    'wind_direction': (0, 360),  # Full arc

    # Highest 24h rain http://www.guinnessworldrecords.com/world-records/greatest-rainfall-24-hours
    'rain': (0, 2000),

    # The current highest wind speed record is 113m/s
    #   https://public.wmo.int/en/media/news/new-world-record-wind-gust
    'wind_speed': (0, 113),

    # Lowest temp: https://www.bbc.co.uk/news/science-environment-25287806 to
    # Highest temp: https://wmo.asu.edu/content/world-highest-temperature
    'temperature': (-94, 56.7),

    # Highest pres.: http://www.guinnessworldrecords.com/world-records/highest-barometric-pressure-
    'pressure': (0, 1083.8)
}


def str_to_epoch(value):
    ''' Converts a date string in the format 'DD MMM yyyy hh:mm' to a epoch timestamp integer

    Args:
        value (str): Datetime string formated as 'DD MMM yyyy hh:mm'

    Returns:
        (int): The converted datetime as POSIX timestamp as a int

    '''
    day, month, year, hhmm = value.split()
    hour, minute = hhmm.split(':')
    return int(datetime.datetime(int(year), MONTH_DICT.index(month)+1, int(day), int(hour),
                                 int(minute)).timestamp())


def validate(value, label):
    ''' Warns the user if the value is out of the expected interval for a given label

    Args:
        value (number): The value to be tested
        label (str): Value identifier
    '''

    start, end = BOUNDS[label]
    if not start <= value <= end:
        logging.getLogger('STD').warning(
            '%s value outside expected interval [%.0f, %.0f]: %.2f', label, start, end, value)


class Measurement:
    ''' A weather measurement on a region

    Args:
        measurement_dict({
            timestamp (number): Epoch based timestamp
            rain (number): Rain (mm)
            wind_speed (number): Wind speed (m/s)
            wind_direction (number): Wind direction (arc degrees 0-360º)
            temperature (number): Temperature (ºC)
            humidity (number): Air humidity (%)
            pressure (number): Air pressure (mbar)
        }): A dictionary where any value is optional and coalesced to zero

    Attributes:
        timestamp (number): Epoch based timestamp
        rain (number): Rain (mm)
        wind_speed (number): Wind speed (m/s)
        wind_direction (number): Wind direction (arc degrees 0-360º)
        temperature (number): Temperature (ºC)
        humidity (number): Air humidity (%)
        pressure (number): Air pressure (mbar)

    '''

    def __init__(self, measurement_dict):
        self.timestamp = measurement_dict.get('timestamp', 0)
        self.rain = measurement_dict.get('rain', 0)
        self.wind_speed = measurement_dict.get('wind_speed', 0)
        self.wind_direction = measurement_dict.get('wind_direction', 0)
        self.temperature = measurement_dict.get('temperature', 0)
        self.humidity = measurement_dict.get('humidity', 0)
        self.pressure = measurement_dict.get('pressure', 0)

    def __iter__(self):
        ''' Yields instance attributes as (key,value)<str,number> tuples '''
        attrs = {
            'timestamp': self.timestamp,
            'rain': self.rain,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'pressure': self.pressure
        }
        for key, value in attrs.items():
            yield (key, value)

    def __str__(self):
        result_dict = dict(self)
        result_dict['timestamp'] = str(datetime.datetime.fromtimestamp(
            result_dict['timestamp']))
        return '\t'.join([
            '{timestamp}',
            'Rain: {rain:5.2f}mm',
            'Wind speed: {wind_speed:5.2f}m/s',
            'Wind direction: {wind_direction:5.2f}º',
            'Temperature: {temperature:5.2f}ºC',
            'Humidity: {humidity:5.2f}%',
            'Pressure: {pressure:5.2f}mbar',
        ]).format(**result_dict)


class Region:
    ''' A weather region

    Args:
        name (str): Region identifier

    Attributes:
        name (str): Region identifier
        measurements (list of Measurement)

    '''

    def __init__(self, name):
        self.name = name.strip()
        self.measurements = []

    def __iter__(self):
        yield (self.name, [dict(measurement) for measurement in self.measurements])

    def __str__(self):
        return 'Region "{}": {} measurements'.format(self.name, len(self.measurements))


class Scraper:
    '''
    Serializes the weather measurements for all meteorological stations

    Attributes:
        stations (list of (str, str)): List of pairs of region name and station id
        regions (list of Region): Stores all fetched and parsed instances
        response_delay (int): Seconds taken in the last request
    '''

    def __init__(self):
        self.regions = []
        self.response_delay = 0
        # Fills regions based on the main URL menu stations list
        self.fetch_stations()

    def fetch_stations(self):
        ''' Returns a list of tuples (name, address) of meteorological stations '''
        logging.getLogger('STD').info('Fetching stations')
        logging.getLogger('STD').debug('[GET] %s', MAIN_URL)
        request = requests.get(MAIN_URL)

        if request.status_code != 200:
            raise HTTPException(request.status_code)

        root = BeautifulSoup(request.text, "html.parser")
        # Get the station names and ids from the items on the list identified by 'lista-estacoes'
        self.stations = [(item.text, item.a.attrs['href'].split('=')[1])
                         for item in root.find('ul', {'id': 'lista-estacoes'}).find_all('li')]

        logging.getLogger('STD').info(
            '%0d station(s) found', len(self.stations))

    def fetch_measurements(self, station):
        ''' Returns a `Region` instance with values based on the station at the passed index '''
        station_id = station[1]

        logging.getLogger('STD').debug(
            '[GET] %s %s', REGION_URL.format(station_id), str({'referer': REFERER_URL}))

        # wait 10x longer than it took them to respond to avoid overwhelming the network
        if FETCH_POLITELY and self.response_delay != 0:
            time.sleep(10 * self.response_delay)

        # Store current time to calculate delay
        request_start = time.time()

        # Request the measurement table with the station URL as the referer
        request = requests.get(REGION_URL.format(station_id),
                               headers={'referer': REFERER_URL})
        self.response_delay = time.time() - request_start

        if request.status_code != 200:
            raise HTTPException(request.status_code)

        root = BeautifulSoup(request.text, "html.parser")

        # Get a list from the headers to match their order later
        label_list = [row.text for row in root.select_one(
            '#tbDadosTelem > tr').find_all('th')]

        measurements = []
        for row in root.select('#tbDadosTelem #tbTelemBody > tr'):
            row_attrs = {}
            # Iters throught table keys and values, filtering out empty lines from the row
            for key, value in zip(label_list, row.findChildren("td", recursive=False)):
                value = value.text.strip()
                if value == "":
                    value = 0
                # Match only the first 4 chars on the dictionary to avoid badly formated headers
                label = next(
                    (LABEL_DICT[_key] for _key in LABEL_DICT if _key[:4] == key[:4]), None)

                # Skip unknown labels
                if label is None:
                    continue

                # Converts the value to the desired format
                value = str_to_epoch(
                    value) if label == 'timestamp' else float(value)

                # Check and warn if the value is not in a valid interval
                validate(value, label)
                row_attrs[label] = value
            measurements.append(Measurement(row_attrs))

        return measurements

    def scrape_next(self):
        ''' Scrap the URL searching for a new region

            Yields:
                (Region): Region instance with all its measurements

        '''
        count = 0
        for station in self.stations:
            logging.getLogger('STD').info('Fetching region #%d', count+1)

            # Initialize a region instance with the current station name
            region = Region(station[0])

            # Fetch measurements from the table
            region.measurements = self.fetch_measurements(station)
            count += 1

            logging.getLogger('STD').debug(
                'Got %s in %.2fms', str(region), self.response_delay)

            yield region

    def scrape_all(self):
        ''' Fills the regions list with all stations measurements '''
        for reg in self.scrape_next():
            self.regions.append(reg)

    def to_json(self):
        '''Returns a JSON string with sorted keys with all measurements for all regions'''
        regions_dict = {}
        for region in self.regions:
            regions_dict.update(dict(region))
        return json.dumps(regions_dict, sort_keys=True, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    setup_logging(tempfile.gettempdir())

    logging.getLogger('STD').info('Starting scraper')

    SCRAPER = Scraper()
    SCRAPER.scrape_all()

    logging.getLogger('STD').info('Finished scraping')

    print(SCRAPER.to_json())
