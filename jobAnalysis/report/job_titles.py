#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import sys
from pathlib import Path

from io import StringIO

import pandas as pd
import numpy as np

sys.path.append(str(Path('.').absolute().parent))

from common.getConnection import connectDB


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


def write_csv(header, results, filename):
    """
    """
    with open(filename, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for date in sorted(results.keys()):
            try:
                rse_number = results[date]['research_soft_eng']
            except KeyError:
                results[date]['research_soft_eng'] = 0

            try:
                rs_number = results[date]['research_soft']
            except KeyError:
                results[date]['research_soft'] = 0
            row = {'Date': date,
                   'Number of Research Software Jobs': results[date]['research_soft'],
                   'Number of RSEs': results[date]['research_soft_eng'],
                   'Total ads': results[date]['total ads']}
            print(row)
            writer.writerow(row)


def get_all_documents(db_conn, filename):

    with open(filename, 'w') as f:
        for doc in db_conn['jobs'].find({'prediction': 1}, {'job_title': 1}):
            job_title = doc['job_title']
            job_title = job_title.rstrip()
            f.write(job_title)
            f.write('\n')
            print(job_title)

if __name__ == "__main__":

    filename = '../../outputs/job_title.csv'
    # header = ['Date', 'Number of Research Software Jobs', 'Number of RSEs', 'Total ads']

    # Connect to the database
    db_conn = connectDB(CONFIG_FILE)

    # Parse the db and get the number of RSE per months
    results = get_all_documents(db_conn, filename)

    # record the results
    # write_csv(header, results, filename)
