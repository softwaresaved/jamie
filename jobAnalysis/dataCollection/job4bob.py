#!/usr/bin/env python
# encoding: utf-8

"""
Script to filter the job list with different parameters and copy that selected jobs into a separated folder
for input into the classifier Bob. Connect to the mongodb and copy file in folder
"""
import os
from shutil import copy2
from include.logger import logger
from include.configParser import ConfigParserPerso as configParser
from job2db import make_sure_path_exists
from job2db import get_connection


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
    # ### Get the variables NAMES from the config.ini file
    config_value = configParser().read_config('./config.ini')
    # config_value = configParser().read_config('./config_dev.ini')

    # Get the folder or the file where the input data are stored
    INPUT_FOLDER = config_value.get('INPUT_FOLDER'.lower(), None)
    DB_ACC_FILE = config_value.get('DB_ACCESS_FILE'.lower(), None)

    sample_value = configParser().read_config('./job4bob_config.ini')
    SAMPLE_FOLDER = sample_value.get('SAMPLE_OUT_FOLDER'.lower(), None)
    # Check if the folder exists and if not, create it
    make_sure_path_exists(SAMPLE_FOLDER)

    access_value = configParser().read_config(DB_ACC_FILE)

    DB_NAME = access_value.get('DB_NAME'.lower(), None)
    DB_COLL = access_value.get('DB_COLLECTION'.lower(), None)
    DB_USER = access_value.get('DB_USERNAME'.lower(), None)
    DB_PASS = access_value.get('DB_PASSWORD'.lower(), None)
    DB_AUTH_DB = access_value.get('DB_AUTH_DB'.lower(), None)
    DB_AUTH_METH = access_value.get('DB_AUTH_METHOD'.lower(), None)

    # Connect to the database
    logger.info('Connection to the database')
    db_jobs = get_connection(DB_NAME, DB_COLL, DB_USER, DB_PASS, DB_AUTH_DB, DB_AUTH_METH)

    for filename in get_valid_id(db_jobs):
        print(filename)
        copy_file(filename, INPUT_FOLDER, SAMPLE_FOLDER)


if __name__ == "__main__":
    main()
