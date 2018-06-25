#!/usr/bin/env python
# encoding: utf-8

"""
Collect the data and analyse the quality of the classifier after the second run

"""
import os
import csv
import argparse
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


def write_csv(results, filename):
    """
    """
    with open(filename, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=results.keys())
        writer.writeheader()
        for k in results:
            print(results[k])
            # try:
            #     rse_number = results[date]['research_soft_eng']
            # except KeyError:
            #     results[date]['research_soft_eng'] = 0
            #
            # try:
            #     rs_number = results[date]['research_soft']
            # except KeyError:
            #     results[date]['research_soft'] = 0
            # row = {'Date': date,
            #        'Number of Research Software Jobs': results[date]['research_soft'],
            #        'Number of RSEs': results[date]['research_soft_eng'],
            #        'Total ads': results[date]['total ads']}
            # writer.writerow(row)


if __name__ == "__main__":

    config_value = configParser()
    config_value.read(CONFIG_FILE)

    # Connect to the database
    db_conn = connectDB(CONFIG_FILE)

    filename = '../../outputs/modelCreation/second_run_classification.csv'
    list_tags_to_match = []

    with open(filename, 'w') as f:
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

        for jobid in list_tags_to_match:
            doc = db_conn.jobs.find_one({'jobid': jobid})
            if doc:
                row = {'jobid': doc['jobid'],
                       'SoftwareJob': doc['prediction'],
                       'source': 'machine_learning'}
                writer.writerow(row)

