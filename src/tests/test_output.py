#!/usr/bin/env python
''' Output tests, in each version of their granularity '''

import json

from ..weather_scraper import Measurement, Region, Scraper

# Shuffled elements to check for consistent ordered outputs
MEASUREMENT_DICT = {
    'timestamp': 5.55,
    'rain': 3.33,
    'pressure': 2.22,
    'wind_direction': 6.66,
    'humidity': 1.11,
    'temperature': 4.44,
    'wind_speed': 7.77
}

MEASUREMENT_DICT_2 = {key: val*2 for key, val in MEASUREMENT_DICT.items()}


def test_measurement():
    ''' Test the parcial json provided by a Measurement instance '''
    mock_instance = Measurement(MEASUREMENT_DICT)
    mock_json_str = json.dumps(dict(mock_instance), sort_keys=True, indent=2)
    expected_str = '''{
  "humidity": 1.11,
  "pressure": 2.22,
  "rain": 3.33,
  "temperature": 4.44,
  "timestamp": 5.55,
  "wind_direction": 6.66,
  "wind_speed": 7.77
}'''
    assert mock_json_str == expected_str


def test_empty_region():
    ''' Test the parcial json provided by a Region instance without measurements '''
    mock_name = 'Test Region'
    mock_instance = Region(mock_name)
    mock_json_str = json.dumps(dict(mock_instance), sort_keys=True, indent=2)
    expected_str = '''{
  "Test Region": []
}'''
    assert mock_json_str == expected_str


def test_region():
    ''' Test the parcial json provided by a Region instance with some measurements'''
    mock_name = 'Test Region'
    mock_instance = Region(mock_name)
    mock_instance.measurements = [Measurement(
        MEASUREMENT_DICT), Measurement(MEASUREMENT_DICT_2)]
    mock_json_str = json.dumps(dict(mock_instance), sort_keys=True, indent=2)
    expected_str = '''{
  "Test Region": [
    {
      "humidity": 1.11,
      "pressure": 2.22,
      "rain": 3.33,
      "temperature": 4.44,
      "timestamp": 5.55,
      "wind_direction": 6.66,
      "wind_speed": 7.77
    },
    {
      "humidity": 2.22,
      "pressure": 4.44,
      "rain": 6.66,
      "temperature": 8.88,
      "timestamp": 11.1,
      "wind_direction": 13.32,
      "wind_speed": 15.54
    }
  ]
}'''
    assert mock_json_str == expected_str


def test_scraper_to_json():
    ''' Test scraper object serialization into a JSON string '''
    region_a = Region('Test Region A')
    region_a.measurements = [Measurement(MEASUREMENT_DICT)]

    region_b = Region('Test Region b')
    region_b.measurements = [Measurement(
        MEASUREMENT_DICT), Measurement(MEASUREMENT_DICT_2)]

    mock_instance = Scraper()
    mock_instance.regions = [region_a, region_b]
    mock_json_str = mock_instance.to_json()

    expected_str = '''{
  "Test Region A": [
    {
      "humidity": 1.11,
      "pressure": 2.22,
      "rain": 3.33,
      "temperature": 4.44,
      "timestamp": 5.55,
      "wind_direction": 6.66,
      "wind_speed": 7.77
    }
  ],
  "Test Region b": [
    {
      "humidity": 1.11,
      "pressure": 2.22,
      "rain": 3.33,
      "temperature": 4.44,
      "timestamp": 5.55,
      "wind_direction": 6.66,
      "wind_speed": 7.77
    },
    {
      "humidity": 2.22,
      "pressure": 4.44,
      "rain": 6.66,
      "temperature": 8.88,
      "timestamp": 11.1,
      "wind_direction": 13.32,
      "wind_speed": 15.54
    }
  ]
}'''
    assert mock_json_str == expected_str
