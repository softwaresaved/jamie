#!/usr/bin/env python
# encoding: utf-8

"""
Python script that converts job htm excerpts downloaded from www.job.ac.uk
Clean the files and insert them into a mongodb
Requirement:
    * config.ini file to collect information for the mongoDB connection
Input:
    * Folder containing html files
"""

import os
import itertools
import errno

import pymongo

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from common.logger import logger
from common.configParser import ConfigParserPerso as configParser

from dataCollection.include.fileProcess import fileProcess
from dataCollection.include.cleaningInformation import OutputRow
from dataCollection.include.summary_day_operation import generateReport


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


logger = logger(name='jobs2db', stream_level=DEBUGGING)


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def get_filename(root_folder, *args):
    """
    Return the name of the file, used as JobId in later processes
    """
    for dirname, subdir, files in os.walk(root_folder):
        for file_ in files:
            if file_ not in itertools.chain(*args):
                yield file_


def get_data(data, infiles):
    """
    Process the data to return a dictionary with the data parsed
    """
    for result in data_from_file(data, infiles):

        yield result


def data_from_file(data, infiles):
    """
    Function to get data from the different files within a folder
    and yield a dictionary containing the parsed information
    """
    fileProc = fileProcess(data)
    for filename in infiles:
        yield fileProc.run(filename)


def create_index(coll, key, unique=False):
    """
    Check if index exists and if not, creates it.
    MongoDB does not recreate it if already existing
    :params:
        :coll: pymongo collection object
        :key: str() the key for the index
        :unique: bool to set up the key as unique or not
    """
    coll.create_index(key, unique=unique)


def get_connection(*args):
    """
    Parse the argument to Pymongo Client
    and return a collection object to connect to the db
    """
    db = args[0]
    coll = args[1]
    c = pymongo.MongoClient()
    try:
        user = args[2]
        passw = args[3]
        db_auth = args[4]
        db_mech = args[5]
        confirmation = c[db].authenticate(user, passw, source=db_auth, mechanism=db_mech)
        logger.info('Authenticated: {}'.format(confirmation))
    except (IndexError, ValueError, TypeError):
        logger.info('Connection to the database without password and authentication')
    return c[db][coll]


def get_db_ids(db):
    """
    Connect to the db and parse all the documents
    return a list with the jobIds
    """
    outlist = list()
    for document in db.find({}, {'jobid': True, '_id': False}):
        outlist.append(document['jobid'])
    return outlist


def main():
    """
    Wrapper around for the data parser from html to mongodb
    """
    # ### CONNECTION TO DB ### #

    # set up access credentials
    config_value = configParser()
    config_value.read(CONFIG_FILE)

    # Get the folder or the file where the input data are stored
    INPUT_FOLDER = config_value['input'].get('INPUT_FOLDER'.lower(), None)
    DB_ACC_FILE = config_value['db_access'].get('DB_ACCESS_FILE'.lower(), None)
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

    # Ensure the indexes are created
    create_index(db_jobs, 'jobid', unique=True)
    create_index(db_jobs, 'IncludeInStudy', unique=False)

    logger.info('Collecting the already recorded jobsIds')
    recorded_jobs_list = get_db_ids(db_jobs)
    logger.info('Nb of already recorded jobs: {}'.format(len(recorded_jobs_list)))

    # Init the report generator
    report = generateReport(db_jobs)

    # Get the list of all files in the folders and only get the ones
    # that are not in the two lists passed in argument
    # That list is the list of jobs that are going to be proceeded
    logger.info('Getting the list of jobsIds to process')
    new_jobs_list = get_filename(INPUT_FOLDER, recorded_jobs_list)

    # ### Start the record ####
    m = 0
    n = 0
    for data in get_data(INPUT_FOLDER, new_jobs_list):
        m +=1
        original_content = data
        # print(original_content.keys())
        report.nb_processed_job +=1
        if report.nb_processed_job % 500 == 0:
            logger.debug('Nb of job processed: {} - recorded: {} - duplicate: {}'.format(report.nb_processed_job,
                                                                                        report.nb_inserted_job,
                                                                                        report.nb_duplicated_job))
        clean_data = OutputRow(data)
        clean_data.clean_row()
        data = clean_data.to_dictionary()
        try:
            if data['invalid_code']:
                n +=1
                print('JobID: {}'.format(data['jobid']))
                try:
                    print('Enhanced: {}'.format(data['enhanced']))
                except KeyError:
                    print('Enhanced: False')
                # print(data.keys())
                print('List of InvalidCodes: {}'.format(data['invalid_code']))
                print('List of Keys: {}'.format(original_content.keys()))
                if data['jobid'] == 'BFW435':
                    # print(original_content['raw_content'])
                    # for k in data:
                    #     print(k)
                    #     print(data[k])
                    #     print('\n')
                    # print('\n')
                    # print('\n')
                    # for k in original_content:
                    #     if k != 'raw_content':
                    #         print(k)
                    #         print(original_content[k])
                    #         print('\n')
                    raise
        except KeyError:
            pass
            # print(original_content.keys())
        # except Exception as e:
        #     pass
        #     logger.info(e)
        # else:
        try:
            db_jobs.insert(data)
            report.nb_inserted_job +=1
        except pymongo.errors.DuplicateKeyError:
            report.nb_duplicated_job +=1
        except pymongo.errors:
            report.nb_mongo_error_job +=1

    # #### Writing report for the cronjob to send by email ####
    print('Number of enhanced jobs: {}'.format(m))
    print('Number of enhanced jobs with one invalid code: {}'.format(n))
    logger.info(report.get_summary())
    logger.info(report.get_current())
    logger.info(report.get_total())
    report.write_csv()


if __name__ == '__main__':
    main()
