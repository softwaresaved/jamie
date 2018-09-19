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
import csv
import json
import itertools
import argparse
import errno

import pymongo

import sys
from pathlib import Path

sys.path.append(str(Path(".").absolute().parent))

from common.logger import logger
from common.getConnection import connectDB
from common.configParser import configParserPerso as configParser

from dataCollection.include.fileProcess import fileProcess
from dataCollection.include.cleaningInformation import OutputRow
from dataCollection.include.summary_day_operation import generateReport


logger = logger(name="jobs2db", stream_level="DEBUG")


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

def data_from_file(input_folder, infiles):
    """
    Function to get data from the different files within a folder
    and yield a dictionary containing the parsed information
    """
    fileProc = fileProcess(input_folder)
    for filename in infiles:
        data = fileProc.run(filename)
        if data:
            yield data

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


def main():
    """
    Wrapper around for the data parser from html to mongodb
    """
    parser = argparse.ArgumentParser(
        description="Transform jobs ads stored in html file into the mongodb"
    )

    parser.add_argument("-c", "--config", type=str, default="config_dev.ini")

    args = parser.parse_args()
    config_file = "../config/" + args.config
    # set up access credentials
    config_value = configParser()
    config_value.read(config_file)
    db_conn = connectDB(config_file)
    # Get the folder or the file where the input data are stored
    INPUT_FOLDER = config_value["input"].get("INPUT_FOLDER".lower(), None)
    # ### Init the processes #####

    # Connect to the database
    logger.info("Connection to the database")
    db_jobs = db_conn["jobs"]
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
    # ### Start the record ####
    n = 0
    right_normal = []
    right_enhanced = []
    right_json = []
    for data in data_from_file(INPUT_FOLDER, new_jobs_list):
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
            logger.debug('\tTotal right jobs: {}'.format(report.nb_processed_job -m))
            logger.debug('\t\tRight normal: {}'.format(len(right_normal)))
            logger.debug('\t\tRight enhanced: {}'.format(len(right_enhanced)))
            logger.debug('\t\tRight json: {}'.format(len(right_json)))
            logger.debug('\tWrong jobs: {}'.format(m))
            logger.debug('\t\tWrong normal: {}'.format(len(wrong_normal)))
            logger.debug('\t\tWrong enhanced: {}'.format(len(wrong_enhanced)))
            logger.debug('\t\tWrong json: {}'.format(len(wrong_json)))
        clean_data = OutputRow(data)
        clean_data.clean_row()
        data_to_record = clean_data.to_dictionary()
        # try:
        #     logger.debug('Employer: {}'.format(data_to_record['employer']))
        #     logger.debug('Uk Uni: {}'.format(data_to_record['uk_university']))
        #     logger.debug('Postcode: {}'.format(data_to_record['uk_postcode']))
        # except KeyError:
        #     pass
        try:
            if len(data_to_record['invalid_code']) >= 3:
                m+=1
                if data_to_record['enhanced'] == 'normal':
                    wrong_normal.append(data_to_record['jobid'])
                elif data_to_record['enhanced'] == 'enhanced':
                    wrong_enhanced.append(data_to_record['jobid'])
                elif data_to_record['enhanced'] == 'json':
                    wrong_json.append(data_to_record['jobid'])

            else:
                n +=1
                if data_to_record['enhanced'] == 'normal':
                    right_normal.append(data_to_record['jobid'])
                elif data_to_record['enhanced'] == 'enhanced':
                    right_enhanced.append(data_to_record['jobid'])
                elif data_to_record['enhanced'] == 'json':
                    right_json.append(data_to_record['jobid'])
        except KeyError:
            n +=1
            if data_to_record['enhanced'] == 'normal':
                right_normal.append(data_to_record['jobid'])
            elif data_to_record['enhanced'] == 'enhanced':
                right_enhanced.append(data_to_record['jobid'])
            elif data_to_record['enhanced'] == 'json':
                right_json.append(data_to_record['jobid'])
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
    logger.debug('\tTotal right jobs: {}'.format(report.nb_processed_job -m))
    logger.debug('\t\tRight normal: {}'.format(len(right_normal)))
    logger.debug('\t\tRight enhanced: {}'.format(len(right_enhanced)))
    logger.debug('\t\tRight json: {}'.format(len(right_json)))
    logger.debug('\tWrong jobs: {}'.format(m))
    logger.debug('\t\tWrong normal: {}'.format(len(wrong_normal)))
    logger.debug('\t\tWrong enhanced: {}'.format(len(wrong_enhanced)))
    logger.debug('\t\tWrong json: {}'.format(len(wrong_json)))

    for type_wrong, inlist in [('wrong_normal.csv', wrong_normal), ('wrong_enhanced', wrong_enhanced),
                               ('wrong_json', wrong_json)]:

        with open(type_wrong, 'w') as f:
            csvwriter = csv.writer(f)
            for i in inlist:
                csvwriter.writerow([i])


if __name__ == "__main__":
    main()
