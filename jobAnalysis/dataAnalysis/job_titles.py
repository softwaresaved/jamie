#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import json
import sys
from pathlib import Path

from io import StringIO

import pandas as pd
import numpy as np

sys.path.append(str(Path('.').absolute().parent))

from common.getConnection import connectDB
from common.textClean import textClean

from get_RSE_per_month import check_if_rse, check_if_rsd


# ## GLOBAL VARIABLES  ###
# # To set up the variable on prod or dev for config file and level of debugging in the
# # stream_level
RUNNING = 'dev'

if RUNNING == 'dev':
    CONFIG_FILE = '../config/config_dev.ini'
    DEBUGGING='DEBUG'
elif RUNNING == 'prod':
    CONFIG_FILE = '../config/config.ini'
    DEBUGGING='INFO'


def write_csv(data, filename):
    header = set()
    list_dict_result = list()
    for result in data:
        print(result['job_title'])
        list_dict_result.append(result)
        for k in result.keys():
            header.add(k)

    with open(filename, 'w') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=list(header))
        writer.writeheader()
        writer.writerows(list_dict_result)

        json.dump(list(data), outfile)

def get_all_documents(db_conn):

    for doc in db_conn['jobs'].find({'description': {'$exists': True},
                                     'placed_on': {'$exists': True},
                                     'job_title': {'$exists': True},
                                     'uk_university': {'$exists': True},
                                     'prediction': {'$exists': True}}, {'_id': False}):
        try:
            job_title = doc['job_title']
            if check_if_rse(cleaner, job_title) or check_if_rsd(cleaner, job_title):
                yield doc
        except KeyError:
            pass

if __name__ == "__main__":

    filename = '../../outputs/job_rse_in_title.csv'

    # Connect to the database
    db_conn = connectDB(CONFIG_FILE)

    # init text_cleaner
    cleaner = textClean(remove_stop=True)

    # Parse the db and get the number of RSE per months
    results = get_all_documents(db_conn)

    # record the results
    write_csv(results, filename)
