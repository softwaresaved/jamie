#!/usr/bin/env python
# -*- coding: utf-8 -*-



import os
import csv
from datetime import datetime
import re

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))


from common.getConnection import connectDB
from common.textClean import textClean

from io import StringIO

import pandas as pd
import numpy as np


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
    # result['total']
    with open(filename, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for date in sorted(results.keys()):
            try:
                rse_number = results[date]['number rse']
            except KeyError:
                results[date]['number rse'] = 0
            row = {'Date': date,
                   'Number of RSEs': results[date]['number rse'],
                   'Total ads': results[date]['total ads']}
            print(row)
            writer.writerow(row)


def check_if_rse(cleaner, txt):

    rse_list = ['research software engineer', 'rse', 'r s e']
    txt = cleaner.clean_text(txt)
    for pos, word in enumerate(txt):
        if word == 'rse':
            return True
        elif word in ['research', 'r']:
            if len(txt) > pos+2:
                if txt[pos+1]  in ['software', 's']:
                    if txt[pos+2] in ['engineer', 'e']:
                        return True
    return False



def remove_suffix_date(s):
    return re.sub(r'(\d)(st|nd|rd|th)', r'\1', str(s))

def transform_valid_date(s):
    return datetime.strptime(s, '%d %B %Y')


def get_month(date):
    """
    retuirn the month from the formating datestring
    23th June 2016
    """
    date_time_obj = transform_valid_date(remove_suffix_date(date))
    # Get only the year and the month and transforming str month into numbered month
    return date_time_obj.strftime('%Y-%m')
    # return ' '.join(date.split(' ')[1:])


def get_all_documents(db_conn, cleaner):
    results = {}
    n = 1
    for doc in db_conn['jobs'].find({}, {'description': 1, 'placed_on': 1}):
        n +=1
        # print(n)
        try:
            doc['description']
            doc['placed_on']
            # results['valid'] = results.get('valid', 0) +1
            date = get_month(doc['placed_on'])
            # results[date]['total ads'] = results[date].get('total ads', 0) +1
            if date in results:
                results[date]['total ads'] += 1
            else:
                results[date] = {'total ads': 1}
            if check_if_rse(cleaner, doc['description']):
                if 'number rse' in results[date]:
                    results[date]['number rse'] += 1
                else:
                    results[date].update({'number rse': 1})
            # print(results)

        except KeyError:
            pass
            # results['invalid'] = results.get('invalid', 0) +1

    return results

if __name__ == "__main__":
    filename = '../../outputs/rse_per_monhts.csv'
    header = ['Date', 'Number of RSEs', 'Total ads']
    # Connect to the database
    db_conn = connectDB(CONFIG_FILE)
    # init text_cleaner
    cleaner = textClean(remove_stop=False)
    # Parse the db and get the number of RSE per months
    results = get_all_documents(db_conn, cleaner)
    # record the results
    write_csv(header, results, filename)
