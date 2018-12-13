#!/usr/bin/env python
# encoding: utf-8

"""
Connecting to the database that contains the classified jobs and apply the corresponding tag to the database that contain the data.
Require a connection to the MySQL database (where the tags are stored) and a connection to the MongoDB, where the
information is stored
"""


import pymongo

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from common.logger import logger
from common.getArgs import getArgs
from common.getConnection import connectMongo, connectMysql


logger = logger(name='dbPreparation')


class mySQL:
    """
    Connection to MySQL using MySQLdb module
    """

    def __init__(self, cursor):
        """
        """
        self.cursor = cursor

    def search_final_classification(self):
        """
        """
        # Option to specify the type of cursor to return. Here use a python dictionary
        self.cursor.execute("""
                            SELECT job.website_id, job.final_classification, answer.value
                            FROM job
                            LEFT JOIN classification ON job.id = classification.job_id
                            JOIN answer ON classification.id = answer.classification_id
                            ORDER BY job.website_id;
                            """)
        for rows in self.cursor.fetchall():
            yield rows


class mongoDB:
    """
    Class to update the document in mongoDB
    """

    def __init__(self, db):
        """
        """
        self.db = db


    def update_list_of_tags(self, coll, row):
        """
        Update the list of classifier
        """
        # If working on a copy of the db, some records will appears with the
        # final_classification set up as None (the obj, not a str()).
        # Just discard them.
        if row['final_classification']:
            # Try and except to only try to insert with jobId without done. If a done is present
            # that means no need to create a new record and raise a DuplicateError
            try:
                self.db[coll].update({'jobid': row['website_id'], 'done': {'$exists': False}},
                                     {'$push': {'tags': row['value']},
                                     '$set': {'SoftwareJob': row['final_classification']}
                                      },
                                     upsert=True)
            except pymongo.errors.DuplicateKeyError:
                print(row)
                pass

    def create_index(self, coll, key, unique=False):
        """
        Check if index exists and if not, creates it.
        MongoDB does not recreate it if already existing
        :params: coll: pymongo collection object
        :params: key: str() the key for the index
        :params: unique: bool to set up the key as unique or not
        """
        self.db[coll].create_index(key, unique=unique)

    def update_done(self, coll):
        """
        Update all the record done during that process with a done key
        """
        self.db[coll].update_many({'done': {'$exists': False}}, {'$set': {'done': True}})


def main():
    """
    """
    # ### CONNECTION TO DB ### #

    description='Get the tags from the mysql database'

    arguments = getArgs(description)
    config_values = arguments.return_arguments()


    db_conn = connectMongo(config_values)

    mongo = mongoDB(db_conn)

    # Create unique index on the JobId to avoid duplicating the records after launching the script
    # several time
    mongo.create_index(config_values.DB_TAG_COLLECTION, 'jobid', unique=True)

    # Connect to the mysql db
    mysql_connector = connectMysql(config_values)
    mysqlConnection = mySQL(mysql_connector)

    # Transferring the data from mysql to mongoDB
    for rows in mysqlConnection.search_final_classification():
        mongo.update_list_of_tags(config_values.DB_TAG_COLLECTION, rows)
    mongo.update_done(config_values.DB_TAG_COLLECTION)


if __name__ == "__main__":
    main()
