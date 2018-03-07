#!/usr/bin/env python
# encoding: utf-8

"""
Script to filter the job list with different parameters and copy that selected jobs into a separated folder
for input into the classifier Bob. Connect to the mongodb and copy file in folder
"""
import os
from shutil import copy2

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from common.logger import logger
from common.configParser import ConfigParserPerso as configParser

from job2db import make_sure_path_exists
from job2db import get_connection


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

logger = logger(name='jobs4bob', stream_level='DEBUG')


def get_valid_id(db):
    """
    Query the db to output the jobID that fit the requirements
    """
    for jobid in db.find({'InvalidCode': {'$exists': False},
                          'TypeRole': {'$nin': ['Master', 'Clerical', 'PhD']}
                         },
                         {'jobid': True, '_id': False}):
        yield jobid['jobid']


def copy_file(filename, inputfolder, outputfolder):
    """
    copy the jobid (which is equal to the filename
    from the inputfolder to the outputfolder
    """
    try:
        copy2(os.path.join(inputfolder, filename), outputfolder)
    except Exception as e:
        raise(e)


def main():
    """
    """
    # set up access credentials
    config_value = configParser()
    config_value.read(CONFIG_FILE)

    # Get the folder or the file where the input data are stored
    INPUT_FOLDER = config_value['input'].get('INPUT_FOLDER'.lower(), None)
    DB_ACC_FILE = config_value['db_access'].get('DB_ACCESS_FILE'.lower(), None)

    SAMPLE_FOLDER = config_value['BOB'].get('SAMPLE_OUT_FOLDER'.lower(), None)
    # Check if the folder exists and if not, create it
    make_sure_path_exists(SAMPLE_FOLDER)

    access_value = configParser()
    access_value.read(DB_ACC_FILE)
    # # MongoDB ACCESS # #
    mongoDB_USER = access_value['MongoDB'].get('db_username'.lower(), None)
    mongoDB_PASS = access_value['MongoDB'].get('DB_PASSWORD'.lower(), None)
    mongoDB_AUTH_DB = access_value['MongoDB'].get('DB_AUTH_DB'.lower(), None)
    mongoDB_AUTH_METH = access_value['MongoDB'].get('DB_AUTH_METHOD'.lower(), None)

    # Get the information about the db and the collections
    mongoDB_NAME = config_value['MongoDB'].get('DB_NAME'.lower(), None)
    mongoDB_JOB_COLL = config_value['MongoDB'].get('DB_JOB_COLLECTION'.lower(), None)

    # ### Init the processes #####

    # Connect to the database
    logger.info('Connection to the database')
    db_jobs = get_connection(mongoDB_NAME, mongoDB_JOB_COLL, mongoDB_USER,
                             mongoDB_PASS, mongoDB_AUTH_DB, mongoDB_AUTH_METH)

    for filename in get_valid_id(db_jobs):
        print(filename)
        copy_file(filename, INPUT_FOLDER, SAMPLE_FOLDER)


if __name__ == "__main__":
    main()
