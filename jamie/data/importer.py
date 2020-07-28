#!/usr/bin/env python
# encoding: utf-8

"""
Python module to import scraped job data in HTML format
downloaded from www.jobs.ac.uk to mongodb, after cleaning.
"""

import os
import csv
import sys
import itertools
import pymongo
from ..logger import logger
from ..config import Config
from ..common.getConnection import connectMongo
from ..scrape.fileProcess import JobFile
from ..scrape.cleaningInformation import OutputRow
from . import valid_employer
from .summary_day_operation import generateReport

logger = logger(name="importer", stream_level="DEBUG")

def get_filename(root_folder, *args):
    """
    Return the name of the file, used as JobId in later processes
    """
    for dirname, subdir, files in os.walk(root_folder):
        for file_ in files:
            if file_ not in itertools.chain(*args):
                yield file_

def data_from_file(input_folder, infiles):
    """
    Function to get data from the different files within a folder
    and yield a dictionary containing the parsed information
    """
    for filename in infiles:
        job = JobFile(input_folder / filename).parse()
        if job:
            yield job

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


def get_db_ids(db):
    """
    Connect to the db and parse all the documents
    return a list with the jobIds
    """
    return db.distinct("jobid")


def main(employer='uk_uni'):
    """
    Wrapper around for the data parser from html to mongodb
    """

    if not valid_employer(employer):
        print("importer: not a valid employer set\n"
              "          use 'jamie list-employers' to see them")
        sys.exit(1)
    c = Config()
    db_conn = connectMongo(c)
    # Get the folder or the file where the input data are stored
    INPUT_FOLDER = c['scrape.folder']
    # ### Init the processes #####

    # Connect to the database
    logger.info("Connection to the database")
    db_jobs = db_conn[c['db.jobs']]
    # Ensure the indexes are created
    create_index(db_jobs, "jobid", unique=True)
    # create_index(db_jobs, 'IncludeInStudy', unique=False)
    create_index(db_jobs, "predicted")

    logger.info("Collecting the already recorded jobsIds")
    recorded_jobs_list = get_db_ids(db_jobs)
    logger.info("Nb of already recorded jobs: {}".format(len(recorded_jobs_list)))

    # Init the report generator
    report = generateReport(db_jobs)

    # Get the list of all files in the folders and only get the ones
    # that are not in the two lists passed in argument
    # That list is the list of jobs that are going to be proceeded
    logger.info("Getting the list of jobsIds to process")
    new_jobs_list = get_filename(INPUT_FOLDER, recorded_jobs_list)

    m = 0
    wrong_enhanced = []
    wrong_normal = []
    wrong_json = []
    empty_file = []
    # ### Start the record ####
    n = 0
    right_normal = []
    right_enhanced = []
    right_json = []
    for data in data_from_file(INPUT_FOLDER, new_jobs_list):
        if db_jobs.find_one({"jobid": data['jobid']}):
            logger.info("Found existing jobid, skipping %s", data['jobid'])
            continue
        report.nb_processed_job += 1
        if report.nb_processed_job % 500 == 0:
            logger.debug(
                """Nb of job processed: {} - recorded: {} - duplicate: {}""".format(
                    report.nb_processed_job,
                    report.nb_inserted_job,
                    report.nb_duplicated_job
                )
            )
            logger.debug('Total jobs: {}'.format(report.nb_processed_job))
            logger.debug('\tTotal right jobs: {}'.format(report.nb_processed_job - m))
            logger.debug('\t\tRight normal: {}'.format(len(right_normal)))
            logger.debug('\t\tRight enhanced: {}'.format(len(right_enhanced)))
            logger.debug('\t\tRight json: {}'.format(len(right_json)))
            logger.debug('\tWrong jobs: {}'.format(m))
            logger.debug('\t\tWrong normal: {}'.format(len(wrong_normal)))
            logger.debug('\t\tWrong enhanced: {}'.format(len(wrong_enhanced)))
            logger.debug('\t\tWrong json: {}'.format(len(wrong_json)))
        clean_data = OutputRow(data, employer=employer)
        clean_data.clean_row()
        data_to_record = clean_data.to_dictionary()
        if 'description' in data_to_record.get('invalid_code', []) or data_to_record['description'] is None:
            logger.error('No description found in %s', data_to_record['filename'])
        try:
            if len(data_to_record['invalid_code']) >= 3:
                m += 1
                if data_to_record['enhanced'] == 'normal':
                    wrong_normal.append(data_to_record['jobid'])
                elif data_to_record['enhanced'] == 'enhanced':
                    wrong_enhanced.append(data_to_record['jobid'])
                elif data_to_record['enhanced'] == 'json':
                    wrong_json.append(data_to_record['jobid'])

            else:
                n += 1
                if data_to_record['enhanced'] == 'normal':
                    right_normal.append(data_to_record['jobid'])
                elif data_to_record['enhanced'] == 'enhanced':
                    right_enhanced.append(data_to_record['jobid'])
                elif data_to_record['enhanced'] == 'json':
                    right_json.append(data_to_record['jobid'])
        except KeyError:
            n += 1
            try:
                if data_to_record['enhanced'] == 'normal':
                    right_normal.append(data_to_record['jobid'])
                elif data_to_record['enhanced'] == 'enhanced':
                    right_enhanced.append(data_to_record['jobid'])
                elif data_to_record['enhanced'] == 'json':
                    right_json.append(data_to_record['jobid'])
            except KeyError:
                empty_file.append(data_to_record['jobid'])
        try:
            db_jobs.insert(data_to_record)
            report.nb_inserted_job += 1
        except pymongo.errors.DuplicateKeyError:
            report.nb_duplicated_job += 1
        except pymongo.errors:
            report.nb_mongo_error_job += 1
    # #### Writing report for the cronjob to send by email ####
    logger.info(report.get_summary())
    logger.info(report.get_current())
    logger.info(report.get_total())
    logger.debug('Total jobs: {}'.format(report.nb_processed_job))
    logger.debug('\tTotal right jobs: {}'.format(report.nb_processed_job - m))
    logger.debug('\t\tRight normal: {}'.format(len(right_normal)))
    logger.debug('\t\tRight enhanced: {}'.format(len(right_enhanced)))
    logger.debug('\t\tRight json: {}'.format(len(right_json)))
    logger.debug('\tWrong jobs: {}'.format(m))
    logger.debug('\t\tWrong normal: {}'.format(len(wrong_normal)))
    logger.debug('\t\tWrong enhanced: {}'.format(len(wrong_enhanced)))
    logger.debug('\t\tWrong json: {}'.format(len(wrong_json)))
    logger.debug('\t\tEmpty file: {}'.format(len(empty_file)))

    for type_wrong, inlist in [('wrong_normal.csv', wrong_normal), ('wrong_enhanced', wrong_enhanced),
                               ('wrong_json', wrong_json), ('empty_file', empty_file)]:

        with open(type_wrong, 'w') as f:
            csvwriter = csv.writer(f)
            for i in inlist:
                csvwriter.writerow([i])


if __name__ == "__main__":
    main()
