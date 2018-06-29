#!/usr/bin/env python
# encoding: utf-8

"""
Collect the data and analyse the quality of the classifier after the second run

"""
import os
import csv
import argparse
from shutil import copy2
from datetime import timedelta

from bson import Code


import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from common.getConnection import connectDB

from common.configParser import configParserPerso as configParser


RUNNING = 'dev'

if RUNNING == 'dev':
    CONFIG_FILE = '../config/config_dev.ini'
elif RUNNING == 'prod':
    CONFIG_FILE = '../config/config.ini'


if __name__ == "__main__":

    config_value = configParser()
    config_value.read(CONFIG_FILE)

    # Connect to the database
    db_conn = connectDB(CONFIG_FILE)

    file_tags = '../../outputs/modelCreation/second_run_classification.csv'
    file_info = '../../outputs/modelCreation/second_run_info.csv'
    list_tags_to_match = []

    with open(file_tags, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=['jobid', 'SoftwareJob', 'tags', 'source'])
        writer.writeheader()
        for doc in db_conn.second_run.find():
            row = {'jobid': doc['jobid'],
                                    'SoftwareJob': doc['SoftwareJob'],
                                    'tags': doc['tags'],
                                    'source': 'second_run'}
            list_tags_to_match.append(doc['jobid'])
            writer.writerow(row)

        for doc in db_conn.tags.find():
            row = {'jobid': doc['jobid'],
                                    'SoftwareJob': doc['SoftwareJob'],
                                    'tags': doc['tags'],
                                    'source': 'first_batch'}
            writer.writerow(row)

        set_keys_of_all_jobs = set()
        for jobid in list_tags_to_match:
            doc = db_conn.jobs.find_one({'jobid': jobid})
            if doc:
                row = {'jobid': doc['jobid'],
                       'SoftwareJob': doc['prediction'],
                       'source': 'machine_learning'}
                writer.writerow(row)
                set_keys_of_all_jobs.update(doc.keys())

    with open(file_info, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=set_keys_of_all_jobs)
        writer.writeheader()
        for jobid in list_tags_to_match:
            doc = db_conn.jobs.find_one({'jobid': jobid})
            if doc:
                writer.writerow(doc)

