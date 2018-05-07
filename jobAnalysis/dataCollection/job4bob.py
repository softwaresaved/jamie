#!/usr/bin/env python
# encoding: utf-8

"""
Script to filter the job list with different parameters and copy that selected jobs into a separated folder
for input into the classifier Bob. Connect to the mongodb and copy file in folder
"""
import os
import argparse
from shutil import copy2

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from common.logger import logger
from common.configParser import ConfigParserPerso as configParser

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
    parser = argparse.ArgumentParser(description='Transform jobs ads stored in html file into the mongodb')

    parser.add_argument('-c', '--config',
                        type=str,
                        default='config_dev.ini')

    args = parser.parse_args()
    config_file = '../config/'+args.config
    db_conn = connectDB(config_file)
    # set up access credentials
    config_value = configParser()
    config_value.read(config_file)
    # Get the folder or the file where the input data are stored
    INPUT_FOLDER = config_value['input'].get('INPUT_FOLDER'.lower(), None)
    DB_ACC_FILE = config_value['db_access'].get('DB_ACCESS_FILE'.lower(), None)

    SAMPLE_FOLDER = config_value['BOB'].get('SAMPLE_OUT_FOLDER'.lower(), None)
    # Check if the folder exists and if not, create it
    make_sure_path_exists(SAMPLE_FOLDER)

    # # MongoDB ACCESS # #
    # Connect to the database
    logger.info('Connection to the database')
    db_jobs = db_conn['jobs']
    # Ensure the indexes are created

    # ### Init the processes #####

    for filename in get_valid_id(db_jobs):
        print(filename)
        copy_file(filename, INPUT_FOLDER, SAMPLE_FOLDER)


if __name__ == "__main__":
    main()
