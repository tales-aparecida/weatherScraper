#!/usr/bin/env python
''' Scraping tests, checks if the serialization matches the webpages.
Big help from [Johannes Fahrenkrug](https://stackoverflow.com/a/28507806) to override the requests
'''

import os
import unittest
from unittest import mock

from ..weather_scraper import Scraper, MAIN_URL, REGION_URL

CURRENT_PATH = os.path.dirname(__file__)

MOCKED_STATION_ID = 1000887
with open(os.path.join(CURRENT_PATH, 'main_url_one_region.html')) as file_handler:
    MAIN_URL_TEXT = file_handler.read()

with open(os.path.join(CURRENT_PATH, 'region_url_text.html')) as file_handler:
    REGION_URL_TEXT = file_handler.read()

with open(os.path.join(CURRENT_PATH, 'expected_str.json')) as file_handler:
    EXPECTED_STR = file_handler.read()


def mocked_requests_get(*args, **kwargs):
    ''' This method will be used by the mock to replace requests.get '''
    class MockResponse:
        ''' Mocks a requests.get response instance '''

        def __init__(self, text, status_code):
            self.text = text
            self.status_code = status_code

    if args[0] == MAIN_URL:
        return MockResponse(MAIN_URL_TEXT, 200)

    if args[0] == REGION_URL.format(MOCKED_STATION_ID):
        return MockResponse(REGION_URL_TEXT, 200)

    return MockResponse(None, 404)


class ScraperTestCase(unittest.TestCase):
    ''' The Scraper test case class, where we patch 'requests.get' with our own method. '''

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_fetch(self, mock_get):
        ''' Test one region measurements scrape '''
        mock_instance = Scraper()
        mock_instance.scrape_all()

        print(mock_instance.to_json())
        assert mock_instance.to_json() == EXPECTED_STR
