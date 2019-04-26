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

from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(".").absolute().parent))

from common.logger import logger
from common.getArgs import getArgs
from common.getConnection import connectMongo
#
# from dataCollection.include.cleaningInformation import OutputRow


logger = logger(name="include_in_study", stream_level="DEBUG")


class IncludeInStudy:
    """
    Check the record in the db and change or add the key
    'include_in_study'. If it meets the given requirements it set
    up the key as 1, 0 if not.
    By default pass all the db but can only passed the records that don't have
    the key 'include_in_study'.
    """

    def __init__(self, db, redo=False):
        """
        :params:
            :db MongoObject(): db connector to the collection containing the jobs


            :redo bool(): to choose if it add a key to document that don't have it (False),
            or passed the entire db and replace the existing key (True). Default: False

        :return:
            :None: apply modifications on each records

        """
        # To remove
        self.requirements = []
        self.db = db
        self.redo = redo
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
            return {'include_in_study': {'$exists': False}, 'invalid_code': {'$exists': False}}
        else:
            return {'invalid_code': {'$exists': False}}

    def _retrieve_doc(self, to_select):
        """
        Return all the documents that match the keys 'to_select'

        :params:
            :to_select dict(): keys to match to return a document

        :return:
            : gen() MongoDB_document(): all the matching documents
        """
        for doc in self.db.find(to_select):
            self.count_all_doc +=1  # inc the global count of all docs
            yield doc

    def _check_inclusion(self, document):
        """
        Check if the document passed meet the requirements and return True if it does
        and False if it doesnt

        :params:
            :document dict(): job record itself as found in the db

        :return:
            :bool(): True if it meets the requirements, False if it does not
        """
        for key in self.requirements:
            try:
                type_check = self.requirements[key]
                if isinstance(type_check, dict):
                    type_check = list(type_check.keys())[0]
                if type_check == '$exists':
                    if str(self.requirements[key]) == 'True':
                        if key not in document:
                            raise KeyError
                    elif str(self.requirements[key]) == 'False':
                        if key in document:
                            raise KeyError

                elif type_check == '$ne':
                    if str(document[key]) == str(self.requirements[key][type_check]):
                        raise KeyError

                elif type_check == '$eq':
                    if str(document[key]) != str(self.requirements[key][type_check]):
                        raise KeyError

                elif type_check == '$in':
                    if isinstance(document[key], list):
                        for item in document[key]:
                            if item not in self.requirements[key][type_check]:
                                raise KeyError
                    else:
                        if document[key] not in self.requirements[key][type_check]:
                            raise KeyError

                elif type_check == '$nin':
                    if isinstance(document[key], list):
                        for item in document[key]:
                            if document[key] in self.requirements[key][type_check]:
                                raise KeyError
                    else:
                        print(self.requirements[key][type_check])
                        if document[key] in self.requirements[key][type_check]:
                            raise KeyError

                else:
                    if str(document[key]) != str(self.requirements[key]):
                        raise KeyError

            except KeyError:   # In case the key is not present it is directly not include
                self.count_not_to_include +=1
                return False
            except TypeError:
                print(document)
                raise
        self.count_to_include +=1
        return True

    def _get_id(self, document):
        """
        Get the jobid from the document

        :params:
            :document dict(): representing the record

        :return:
            :str(): the jobid of the document
        """
        return document['jobid']

    def _update_record(self, document, include_in_study):
        """
        Update the record with the value_include in include_in_study

        :params:
            :document dict(): record from the db
            :include_in_study bool: value to insert in the key include_in_study

        :return:
            :None: update directly the matching document in the db if found with the
            jobid str() key.
        """
        jobid = self._get_id(document)
        # self._output_count()
        self.db.update_one({'jobid': jobid},
                           {'$set': {'include_in_study': include_in_study}},
                           upsert=False)

    def _output_count(self):
        """
        print the different counts set in __init__
        :params:
            :None: use the self.counts
        :return:
            :print: results of the self.counts
        """
        logger.info('Total documents parsed: {}'.format(self.count_all_doc))
        logger.info('Documents to include in the study: {}'.format(self.count_to_include))
        logger.info('Document Not included in study: {}'.format(self.count_not_to_include))

    def add_in_uk(self, document):
        """
        Add the in_uk key as True in the database if it is from a UK extra_location
        """
        try:
            if document['extra_location'] in ["Northern England",
                                              "London",
                                              "Midlands of England",
                                              "Scotland",
                                              "South West England",
                                              "South East England",
                                              "Wales",
                                              "Republic of Ireland",
                                              "Northern Ireland"]:

                self.db.update_one({'jobid': document['jobid']},
                                   {'$set': {'in_uk': True}},
                                   upsert=False)
            return
        except KeyError:
            pass
        self.invalid_process.append('in_uk')

    def add_in_range(self, document):
        """
        Add a key 'in_range' for document that are between 2014 and 2018
        It parse the key 'placed_on' and check if the datetime is within that range
        add a key True if it is the case
        """
        try:
            date_job = document['placed_on']
            date_2015 = datetime(2015, 1, 1, 0, 0, 0)
            date_2018= datetime(2018, 1, 1, 0, 0, 0)
            if date_job >= date_2015 and date_job <= date_2018:
                self.db.update_one({'jobid': document['jobid']},
                                   {'$set': {'in_range': True}},
                                   upsert=False)
                return
        except KeyError:
            pass
        self.invalid_process.append('in_range')

    def add_len_description(self, document):
        """
        Add a key 'len_description' if the text is above 100 words.
        """
        try:
            description = document['description']
            if len(description.split()) > 100:
                self.db.update_one({'jobid': document['jobid']},
                                   {'$set': {'len_description': True}},
                                   upsert=False)
                return
        except KeyError:
            pass
        self.invalid_process.append('len_description')

    def add_academic(self, document):
        not_aca = False
        try:
            type_role = document['type_role']
            for role in type_role:   # this is a list of roles
                if role in ['PhD', 'Masters', 'Clerical', 'Craft or Manual']:
                    not_aca = True
            if not_aca is False:

                self.db.update_one({'jobid': document['jobid']},
                                   {'$set': {'academic_role': True}},
                                   upsert=False)
                return
        except (KeyError, TypeError):
            pass

        self.invalid_process.append('academic_role')

    def add_invalid_key(self, document):
        """
        Add the list of invalid key for document that have some
        errors in the preprocess
        """
        if len(self.invalid_process) == 0:
            self.db.update_one({'jobid': document['jobid']},
                               {'$set': {'include_in_study': True}},
                               upsert=False)
            return
        else:
            self.db.update_one({'jobid': document['jobid']},
                               {'$set': {'invalid_process': self.invalid_process}},
                               upsert=False)

    def run(self):
        """
        Run the class
        """
        to_select = self._select_records()

        logger.info('Start the process')
        for document in self._retrieve_doc(to_select):
            self.invalid_process = list()
            # value_include = self._check_inclusion(document)
            # self._update_record(document, value_include)
            self.add_in_uk(document)
            self.add_in_range(document)
            self.add_len_description(document)
            self.add_academic(document)
            self.add_invalid_key(document)

        self._output_count()


def main():
    """
    Wrapper around for the include_in_study or not
    """
    description="Parse the database and add or update a key 'to_include' as True or False if document meet the requirements"
    arguments = getArgs(description)
    config_values = arguments.return_arguments()

    db_conn = connectMongo(config_values)
    # ### Init the processes #####

    # Connect to the database
    logger.info("Connection to the database")
    db_jobs = db_conn[config_values.DB_JOB_COLLECTION]

    logger.info('Create the key `include_in_study`')
    to_include = IncludeInStudy(db_jobs, redo=config_values.relaunch_include)
    to_include.run()


if __name__ == "__main__":
    main()
