#!/usr/bin/env python
# encoding: utf-8

"""
Python module to import scraped job data in HTML format
downloaded from www.jobs.ac.uk to mongodb, after cleaning.
"""

import os
import sys
import itertools
import pymongo
from collections import defaultdict
from ..logger import logger
from ..config import Config
from ..common.getConnection import connectMongo
from ..scrape.fileProcess import JobFile
from . import valid_employer

logger = logger(name="importer", stream_level="DEBUG")
REPORT_INTERVAL = 1000  # report progress of database import every N jobs

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


def main(config, employer='uk_uni'):
    """Import data from HTML to MongoDB

    Parameters
    ----------
    config : jamie.config.Config
        Configuration
    employer : str, optional
        Employer set to use, by default uk_uni
    """

    if not valid_employer(employer):
        print("importer: not a valid employer set\n"
              "          use 'jamie list-employers' to see them")
        sys.exit(1)

    db_conn = connectMongo(config)
    db_jobs = db_conn[config['db.jobs']]
    create_index(db_jobs, "jobid", unique=True)  # faster searches for "jobid"

    logger.info("Collecting the already recorded jobs")
    recorded_jobs_list = get_db_ids(db_jobs)
    logger.info("Already recorded jobs: {}".format(len(recorded_jobs_list)))

    # new_jobs_list has only the jobs not in recorded_jobs_list
    new_jobs_list = get_filename(config['scrape.folder'], recorded_jobs_list)
    njobs = defaultdict(int)
    for data in data_from_file(config['scrape.folder'], new_jobs_list):
        if njobs['inserted'] % REPORT_INTERVAL == 0:
            logger.debug("Progress %s", njobs)
        try:
            db_jobs.insert(data)
            njobs['inserted'] += 1
        except pymongo.errors.DuplicateKeyError:
            njobs['duplicate'] += 1
        except pymongo.errors:
            njobs['mongo_error'] += 1
    logger.info("Final import state %s", njobs)
