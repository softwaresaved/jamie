#!/usr/bin/env python
# encoding: utf-8

"""
Python module to import scraped job data in HTML format
downloaded from www.jobs.ac.uk to mongodb, after cleaning.
"""

import sys
import pymongo
from collections import defaultdict
from ..logger import logger
from ..common.getConnection import connectMongo
from ..scrape.fileProcess import JobFile
from . import valid_employer

logger = logger(name="importer", stream_level="DEBUG")
REPORT_INTERVAL = 1000  # report progress of database import every N jobs


def _import_iterator(input_folder, skip):
    """Iterate over JobFile data

    Parameters
    ----------
    input_folder : Path
        Input folder containing job data in HTML format
    skip : List[str]
        List of file stems (without suffix) to skip. Usually this is
        the set of already recorded jobids

    Yields
    ------
    dict
        Job data in a dictionary
    """
    for filename in (f for f in input_folder.glob("*") if f.stem not in skip):
        job = JobFile(input_folder / filename).parse()
        if job:
            yield job


def main(config, employer="uk_uni"):
    """Import data from HTML to MongoDB

    Parameters
    ----------
    config : jamie.config.Config
        Configuration
    employer : str, optional
        Employer set to use, by default uk_uni
    """

    if not valid_employer(employer):
        print(
            "importer: not a valid employer set\n"
            "          use 'jamie list-employers' to see them"
        )
        sys.exit(1)

    db_conn = connectMongo(config)
    db_jobs = db_conn[config["db.jobs"]]
    db_jobs.create_index("jobid", unique=True)  # faster searches for "jobid"

    recorded_jobs = db_jobs.distinct("jobid")
    logger.info("Already recorded jobs: {}".format(len(recorded_jobs)))
    njobs = defaultdict(int)
    for data in _import_iterator(config["scrape.folder"], skip=recorded_jobs):
        if njobs["inserted"] % REPORT_INTERVAL == 0:
            logger.debug("Progress %s", njobs)
        try:
            db_jobs.insert(data)
            njobs["inserted"] += 1
        except pymongo.errors.DuplicateKeyError:
            njobs["duplicate"] += 1
        except pymongo.errors:
            njobs["mongo_error"] += 1
    logger.info("Final import state %s", njobs)
