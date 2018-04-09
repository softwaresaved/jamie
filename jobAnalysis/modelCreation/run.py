#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from io import StringIO

import pandas as pd
import numpy as np


from include.features import get_train_data
from include.model import nested_cross_validation, adaboost


from common.logger import logger

logger = logger(name='prediction_run', stream_level='DEBUG')

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



if __name__ == "__main__":

    job_ids, X, y = get_train_data()
    adaboost(X, y)
    # model_name, model_best_params, model = nested_cross_validation(X, y, 'description-job_title', nbr_folds=2)


        # vectorising_data = vectorProcess(dict_name='_'.join([collection_data, input_field, input_data, operation, 'vector']))
        # m=0
        # n=0
        # nbr_yes = 0
        # nbr_no = 0
        # db_doc = db_conn.return_collection(collection=collection_data)
        # for document in db_doc.find({'input_field': input_field,
        #                              'operation': operation,
        #                              'input_data': input_data,
        #                              'data': {'$exists': True}}):
        #     m+=1
        #     try:
        #         data_vector = vectorising_datr.get_vector(document['data'], update_dict=False)
        #         data_sparse_matrix = training_set.create_sparse_matrix(data_vector, training_set.max_vector)
        #         data_tfidf = training_set.transform_tfidf(data_sparse_matrix)
        #
        #
        #         prediction = model.predict(data_tfidf)[0]
        #         # prediction = model.predict(data_sparse_matrix)[0]
        #         if prediction == 0:
        #             prediction = 'No'
        #         if prediction == 1:
        #             prediction = 'Yes'
        #         db_prediction.update({'jobid': document['JobId'],
        #                                 'input_field': input_field,
        #                                 'input_data': input_data,
        #                                 'operation': operation,
        #                                 'model': model_name,
        #                                 'folding': name_fold,
        #                                 'params': model_best_params},
        #                                 {'$set': {'prediction': prediction}},
        #                                 upsert=True)
        #         n+=1
        #         if prediction == 'Yes':
        #             nbr_yes +=1
        #         if prediction == 'No':
        #             nbr_no +=1
        #
        #         if m % 5000 == 0:
        #             print('Number of document processed: {}'.format(m))
        #             print('Number of document classified: {}'.format(n))
        #             print('Number of Yes: {}'.format(nbr_yes))
        #             print('Number of No: {}'.format(nbr_no))
        #             print('\n')
        #     except KeyError:
        #         pass
        #     except ValueError:
        #         pass
