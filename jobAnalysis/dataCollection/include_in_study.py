
#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Script to parse the results in the database and check if they meet the
requirements set up in config.ini #TODO and add a key.
It it meets the requirement the key 'include_in_study' = 1, if not = 0
It will only add a key to documents that does not have it. Default behaviour
It can also redo all documents in the db in case the requirements changed.

It doesnt use the aggregation function in MongoDB because it is inconsistent
to what it is supposed to output. Rather, output all the records. In consequence,
it is a slow script but ensure it has the expected results.
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


logger = logger(name="include_in_study", stream_level="DEBUG")


# TODO, move this list of requirements into the config file when reworked

requirements = {}


class IncludeInStudy:
    """
    Check the record in the db and change or add the key
    'include_in_study'. If it meets the given requirements it set
    up the key as 1, 0 if not.
    By default pass all the db but can only passed the records that don't have
    the key 'include_in_study'.
    """

    def __init__(self, db, requirements, redo=False):
        """
        :params:
            :db MongoObject(): db connector to the collection containing the jobs

            :requirements dict():  dictionary containing the requirements
            that needs to be checked

            :redo bool(): to choose if it add a key to document that don't have it (False),
            or passed the entire db and replace the existing key (True). Default: False

        :return:
            :None: apply modifications on each records

        """
        self.requirements = requirements
        self.db = db
        self.jobid = jobid
        # A counter for all the documents parsed
        self.count_all_doc = 0
        # A counter for all the documents with to_include = True
        self.count_to_include = 0
        # A counter for all the documents with to_include = False
        self.count_not_to_include = 0

    def _select_records(self):
        """
        Decide which records is selected based on the value of redo
        :params:
            None: use the value of self.redo from __init__()
        :return:
            dict(): Empty dictionary if self.redo = True, and dict with '$exists'
            if self.redo = False
        """
        if self.redo is False:
            return {'include_in_study' {'$exists': False}}
        else:
            return {}

    def _retrieve_doc(self, to_select):
        """
        Return all the documents that match the keys 'to_select'

        :params:
            :to_select dict(): keys to match to return a document

        :return:
            : gen() MongoDB_document(): all the matching documents
        """
        for doc in self.db.find(to_select):
            yield doc

    def

    def run(self):
        """
        Run the class
        """
        to_select = self._select_records()

        for document in self.retrieve_doc(to_select):
            value_include = self._check_inclusion(document)




def main():
    """
    Wrapper around for the include_in_study or not
    """
    parser = argparse.ArgumentParser(
        description="Parse the database and add or update a key 'to_include' as True or False if document meet the requirements"
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
    to_include = IncludeInStudy(db, requirements, redo=True)
    to_include.run()

if __main__():
    main()


