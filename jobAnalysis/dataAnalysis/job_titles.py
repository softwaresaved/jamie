#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import json
import sys
from pathlib import Path
from shutil import copy2

import argparse
from io import StringIO

import pandas as pd
import numpy as np

sys.path.append(str(Path('.').absolute().parent))

from common.configParser import configParserPerso as configParser
from common.getConnection import connectDB
from common.textClean import textClean

from get_RSE_per_month import check_if_rse, check_if_rsd


def write_csv(data, filename):
    total_0 = 0
    total_1 = 0
    total_jobs = 0
    header = set()
    list_dict_result = list()
    list_of_file_to_move = list()
    for result in data:
        total_jobs +=1
        print(result['job_title'], result['prediction'])
        if result['prediction'] == 1:
            total_1 +=1
        else:
            total_0 +=1
        list_dict_result.append(result)
        for k in result.keys():
            header.add(k)
        list_of_file_to_move.append(result['jobid'])

    print('total jobs: {}'.format(total_jobs))
    print('total Software ones: {}'.format(total_1))
    print('total Not Software ones: {}'.format(total_0))
    with open(filename, 'w') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=list(header))
        writer.writeheader()
        writer.writerows(list_dict_result)

        json.dump(list(data), outfile)
    return list_of_file_to_move


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

    # Parsing the config file name
    parser = argparse.ArgumentParser(description='Collect information from all the dataset and create csv file for being used in jupyter notebook without access to the databases')
    parser.add_argument('-c', '--config',
                        type=str,
                        default='config_dev.ini')
    args = parser.parse_args()
    config_file = '../config/' + args.config
    if config_file[-3:] != 'ini':
        config_file += '.ini'

    config_value = configParser()
    config_value.read(config_file)
    in_folder = config_value["input"].get("INPUT_FOLDER".lower(), None)
    out_folder = '../../outputs/jobs_rse_in_title/'
    # Connect to the database
    db_conn = connectDB(config_file)

    # init text_cleaner
    cleaner = textClean(remove_stop=True)

    # Parse the db and get the number of RSE per months
    results = get_all_documents(db_conn)

    # record the results
    list_filename = write_csv(results, filename)
    for i in list_filename:
        print(i)
        copy2('{}/{}'.format(in_folder, i), out_folder)# '{}{}'.format(out_folder, i))

