#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import sys
import random
from pathlib import Path
from shutil import copy2

import pandas as pd
import numpy as np

sys.path.append(str(Path('.').absolute().parent))

from common.logger import logger
from common.getArgs import getArgs
from common.getConnection import connectMongo


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
    rsj_set_admin = set()
    rsj = 0
    nrsj_set = set()
    nrsj_set_admin = set()
    nrsj = 0
    no_pred = 0
    for doc in db_conn['jobs'].find({'description': {'$exists': True},
                                     'placed_on': {'$exists': True},
                                     'prediction': {'$exists': True},
                                     'prediction': {'$ne': 'None'},
                                     'not_student': True,
                                     'uk_university': {'$exists': True}}):
        if len(doc['description']) > 150:
            if doc['prediction'] == 1:
                if 'Administrative' not in doc['subject_area']:
                    rsj +=1
                    rsj_set.add(doc['jobid'])
                else:
                    rsj +=1
                    rsj_set_admin.add(doc['jobid'])

            elif doc['prediction'] == 0:
                if 'Administrative' not in doc['subject_area']:
                    nrsj +=1
                    nrsj_set.add(doc['jobid'])
                else:
                    nrsj +=1
                    nrsj_set_admin.add(doc['jobid'])

            else:
                no_pred +=1
    print('Software Job: {}'.format(rsj))
    print('NOT Software Job: {}'.format(nrsj))
    print('NOT prediction: {}'.format(no_pred))
    print('Total of jobs: {}'.format(str(rsj+nrsj+no_pred)))
    return rsj_set,rsj_set_admin,  nrsj_set, nrsj_set_admin

def get_sample(*args, **kwargs):
    """
    """
    size_rsj = int(kwargs['nbr_job']* kwargs['percentage_rsj'])
    size_nrsj = int(kwargs['nbr_job'] - size_rsj)

    print('Size rsj: {}'.format(size_rsj))
    print('Size nrsj: {}'.format(size_nrsj))

    list_rsj = random.sample(args[0], int(size_rsj*0.9)) + random.sample(args[1], int(size_rsj*0.1))
    list_nrsj = random.sample(args[2], int(size_nrsj*0.9)) + random.sample(args[3], int(size_nrsj*0.1))

    return list_rsj, list_nrsj


if __name__ == "__main__":

    arguments = getArgs(description)
    config_values = arguments.return_arguments()

    db_conn = connectMongo(config_values)
    # Get the folder or the file where the input data are stored
    # ### Init the processes #####

    # Connect to the database
    logger.info("Connection to the database")
    db_jobs = db_conn[config_values.DB_JOB_COLLECTION]

    in_folder = config_values.INPUT_FOLDER
    out_folder = '../../outputs/jobs_checking_set/'
    filename =  '../../outputs/uniqueValue/id_list_new_sample.csv'

    set_research_soft, set_research_soft_admin, set_not_research_soft, set_not_research_soft_admin = get_all_documents(db_conn)

    sampled_rsj, sample_not_rsj = get_sample(set_research_soft, set_research_soft_admin, set_not_research_soft, set_not_research_soft_admin,  percentage_rsj=0.7, nbr_job=200)

    for i in sampled_rsj + sample_not_rsj:
        print(i)
        copy2('{}/{}'.format(in_folder, i), out_folder)
