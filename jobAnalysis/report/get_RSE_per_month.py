#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import sys
import re
from datetime import datetime
from pathlib import Path

from io import StringIO

import pandas as pd
import numpy as np

sys.path.append(str(Path('.').absolute().parent))

from common.getConnection import connectDB
from common.textClean import textClean


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


def check_if_rse(cleaner, txt):

    txt = cleaner.clean_text(txt)
    to_return = False
    for pos, word in enumerate(txt):
        if word == 'rse':
            to_return = 'research_soft_eng'
            return to_return
        elif word in ['research', 'r']:
            try:
                if txt[pos+1]  in ['software', 's']:
                    to_return = 'research_soft'
                    if txt[pos+2] in ['engineer', 'e']:
                        to_return = 'research_soft_eng'
            except IndexError:
                pass
    return to_return


def remove_suffix_date(s):
    return re.sub(r'(\d)(st|nd|rd|th)', r'\1', str(s))


def transform_valid_date(s):
    return datetime.strptime(s, '%d %B %Y')


def get_month(date):
    """
    return the month from the formatting datestring
    23th June 2016
    """
    date_time_obj = transform_valid_date(remove_suffix_date(date))
    # Get only the year and the month and transforming str month into numbered month
    return date_time_obj.strftime('%Y-%m')


def get_all_documents(db_conn, cleaner):
    results = {}
    for doc in db_conn['jobs'].find({}, {'description': 1, 'placed_on': 1}):
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
            match_soft = check_if_rse(cleaner, doc['description'])
            if match_soft:
                if match_soft in results[date]:
                    results[date][match_soft] += 1
                else:
                    results[date].update({match_soft: 1})
                # If the match_soft is equal to research_soft_eng it means it is also equal to research_soft
                if match_soft == 'research_soft_eng':
                    if 'research_soft' in results[date]:
                        results[date]['research_soft'] +=1
                    else:
                        results[date].update({'research_soft': 1})

        except KeyError:
            # results['invalid'] = results.get('invalid', 0) +1
            pass

    return results


if __name__ == "__main__":

    filename = '../../outputs/research_software_per_month.csv'
    header = ['Date', 'Number of Research Software Jobs', 'Number of RSEs', 'Total ads']

    # Connect to the database
    db_conn = connectDB(CONFIG_FILE)

    # init text_cleaner
    cleaner = textClean(remove_stop=False)

    # Parse the db and get the number of RSE per months
    results = get_all_documents(db_conn, cleaner)

    # record the results
    write_csv(header, results, filename)
