#!/usr/bin/env python
# encoding: utf-8

"""
Python module to import scraped job data in HTML format
downloaded from www.jobs.ac.uk to mongodb, after cleaning.
"""

import pymongo
from collections import defaultdict
from ..logger import logger
from ..lib import connect_mongo
from ..scrape.process import JobFile

logger = logger(name="importer", stream_level="DEBUG")
REPORT_INTERVAL = 10000  # report progress of database import every N jobs


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
        job = JobFile(filename).parse()
        if job.data:
            yield job.data


def log_missing_attributes(data, attributes):
    for attr in attributes:
        if attr not in data:
            logger.warning("Missing {} in {}".format(attr, data["jobid"]))


def main(config, dry_run=False):
    """Import data from HTML to MongoDB

    Parameters
    ----------
    config : jamie.config.Config
        Configuration
    dry_run: bool, optional
        If True, does not insert jobs into database, only logs missing attributes

    Returns
    -------
    dict, optional
        If not a dry run, returns the number of jobs inserted, duplicates and errors
    """

    if not dry_run:
        db_conn = connect_mongo(config)
        db_jobs = db_conn[config["db.jobs"]]
        db_jobs.create_index("jobid", unique=True)  # faster searches for "jobid"

        recorded_jobs = db_jobs.distinct("jobid")
        logger.info("Already recorded jobs: {}".format(len(recorded_jobs)))
        njobs = defaultdict(int)
        for data in _import_iterator(config["scrape.folder"], skip=recorded_jobs):
            if njobs["inserted"] % REPORT_INTERVAL == 0:
                logger.debug(
                    "Progress %s",
                    ", ".join("{} {}".format(v, k) for k, v in njobs.items()),
                )

            try:
                db_jobs.insert(data)
                njobs["inserted"] += 1
            except pymongo.errors.DuplicateKeyError:
                njobs["duplicate"] += 1
            except pymongo.errors:
                njobs["mongo_error"] += 1
        logger.info("Final import state %s", njobs)
        return njobs
    else:
        for data in _import_iterator(config["scrape.folder"], skip=[]):
            log_missing_attributes(data, ["description", "job_title", "date"])
