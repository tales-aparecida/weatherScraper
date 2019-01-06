#!/usr/bin/env python
'''
This file handles the tool log output to file and console
'''

import logging
import logging.config
import os

LOG_FILENAME = 'weather_scraper.log'
LOG_FILE_PERMISSION = 0o744


def setup_logging(out_path):
    ''' Setup the logging handler to append a file and output to console '''

    if not os.path.exists(out_path):
        os.mkdir(out_path)

    log_path = os.path.join(out_path, LOG_FILENAME)
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '[%(asctime)s] %(levelname)-7s   %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'file': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.FileHandler',
                'filename': log_path
            },
        },
        'loggers': {
            'STD': {
                'level': 'DEBUG',
                'handlers': ['file', 'console'],
            },
        }
    })
    logging.getLogger('STD').debug('Log dictConfig set')

    logging.getLogger('STD').debug('Updating log file permission')
    os.chmod(log_path, LOG_FILE_PERMISSION)

    logging.getLogger('STD').debug('Log setup done')

    logging.getLogger('STD').info('Log can be found at %s', log_path)
