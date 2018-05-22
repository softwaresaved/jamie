#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import sys
import random
from pathlib import Path
from shutil import copy2
from io import StringIO

import pandas as pd
import numpy as np

sys.path.append(str(Path('.').absolute().parent))

from common.getConnection import connectDB

from common.configParser import configParserPerso as configParser


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


def get_all_documents(db_conn):
    results = {}
    rsj_set = set()
    rsj = 0
    nrsj_set = set()
    nrsj = 0
    no_pred = 0
    for doc in db_conn['jobs'].find({'description': {'$exists': True},
                                     'placed_on': {'$exists': True},
                                     'prediction': {'$exists': True},
                                     'extra_location_s': {'$exists': True},
                                     'uk_university': {'$exists': True}}):
        if len(doc['description']) > 150:
            if doc['prediction'] == 1:
                rsj +=1
                rsj_set.add(doc['jobid'])
            elif doc['prediction'] == 0:
                nrsj +=1
                nrsj_set.add(doc['jobid'])
            else:
                no_pred +=1
    print('Software Job: {}'.format(rsj))
    print('NOT Software Job: {}'.format(nrsj))
    print('NOT prediction: {}'.format(no_pred))
    print('Total of jobs: {}'.format(str(rsj+nrsj+no_pred)))
        # try:
        #     doc['description']
        #     doc['placed_on']
        #     # results['valid'] = results.get('valid', 0) +1
        #     date = get_month(doc['placed_on'])
        #     # results[date]['total ads'] = results[date].get('total ads', 0) +1
        #     if date in results:
        #         results[date]['total ads'] += 1
        #     else:
        #         results[date] = {'total ads': 1}
        # except KeyError:
        #     # results['invalid'] = results.get('invalid', 0) +1
        #     pass
        #
    return rsj_set, nrsj_set

def get_sample(*args, **kwargs):
    """
    """
    size_rsj = int(kwargs['nbr_job']* kwargs['percentage_rsj'])
    size_nrsj = int(kwargs['nbr_job'] - size_rsj)

    print('Size rsj: {}'.format(size_rsj))
    print('Size nrsj: {}'.format(size_nrsj))


    list_rsj = random.sample(args[0], size_rsj)
    list_nrsj = random.sample(args[1], size_nrsj)
    return list_rsj, list_nrsj





if __name__ == "__main__":

    config_value = configParser()
    config_value.read(CONFIG_FILE)

    # Connect to the database
    db_conn = connectDB(CONFIG_FILE)

    in_folder = config_value['input']['INPUT_FOLDER']
    out_folder = '../../outputs/jobs_training-set-collector/'
    filename =  '../../outputs/uniqueValue/id_list_new_sample.csv'

    set_research_soft, set_not_research_soft = get_all_documents(db_conn)

    sampled_rsj, sample_not_rsj = get_sample(set_research_soft, set_not_research_soft, percentage_rsj=0.7, nbr_job=500)

    for i in sampled_rsj + sample_not_rsj:
        print(i)
        copy2('{}/{}'.format(in_folder, i), out_folder)
