#!/usr/bin/env python
# encoding: utf-8

"""
Python script that converts job htm excerpts downloaded from www.job.ac.uk
Clean the files and insert them into a mongodb
Requirement:
    * config.ini file to collect information for the mongoDB connection
Input:
    * Folder containing html and json files
"""

import os
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

    # ### Start the record ####
    n = 0
    o = 0
    p = 0
    for data in data_from_file(INPUT_FOLDER, new_jobs_list):
        report.nb_processed_job += 1
        if report.nb_processed_job % 500 == 0:
            logger.debug(
                """Nb of job processed: {} - recorded: {} - duplicate: {}
                        - Nb of normal jobs: {}
                        - Nb of enhanced jobs: {}
                        - Nb of json jobs:{}""".format(
                    report.nb_processed_job,
                    report.nb_inserted_job,
                    report.nb_duplicated_job,
                    report.nb_normal_job,
                    report.nb_enhanced_job,
                    report.nb_json_job
                )
            )
        clean_data = OutputRow(data)
        clean_data.clean_row()
        data = clean_data.to_dictionary()
        try:
            if data['enhanced'] == 'json':
                report.nb_json_job +=1
            elif data['enhanced'] == 'normal':
                report.nb_normal_job +=1
            elif data['Enhanced'] == 'enhanced':
                report.nb_enhanced_job +=1
            else:
                pass
        except KeyError:
            pass
        try:
            if data["invalid_code"]:
                report.invalid_code_job +=1
                print("JobID: {}".format(data["jobid"]))
                try:
                    print("Enhanced: {}".format(data["enhanced"]))
                except KeyError:
                    print("Enhanced: False")
                print("List of InvalidCodes: {}".format(data["invalid_code"]))
                print("List of Keys: {}".format(original_content.keys()))

        except KeyError:
            pass
        try:
            db_jobs.insert(data)
            report.nb_inserted_job += 1
        except pymongo.errors.DuplicateKeyError:
            report.nb_duplicated_job += 1
        except pymongo.errors:
            report.nb_mongo_error_job += 1
        #
    # #### Writing report for the cronjob to send by email ####
    print("Number of enhanced jobs: {}".format(m))
    print("Number of enhanced jobs with one invalid code: {}".format(n))
    logger.info(report.get_summary())
    logger.info(report.get_current())
    logger.info(report.get_total())
    report.write_csv()


if __name__ == "__main__":
    main()
