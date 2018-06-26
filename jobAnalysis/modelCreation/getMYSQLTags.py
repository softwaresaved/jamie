#!/usr/bin/env python
# encoding: utf-8

"""
Connecting to the database that contains the classified jobs and apply the corresponding tag to the database that contain the data.
Require a connection to the MySQL database (where the tags are stored) and a connection to the MongoDB, where the
information is stored
"""

import argparse

import pymongo
import pymysql as mdb

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from common.logger import logger
from common.getConnection import connectDB
from common.configParser import configParserPerso as configParser


logger = logger(name='dbPreparation')


class mySQL:
    """
    Connection to MySQL using MySQLdb module
    """

    def __init__(self, **kwargs):
        """
        """
        self._host = kwargs.get('host', 'localhost')
        self._db_user = kwargs.get('user', None)
        self._db_pass = kwargs.get('password', None)
        self._db = kwargs.get('db', None)
        self.conn = self.connect(self._host, self._db_user, self._db_pass, self._db)
        self.cursor = self.cursor(self.conn)

    def connect(self, *args, **kwargs):
        """
        """
        return mdb.connect(*args)

    def cursor(self, connector):
        """
        """
        return connector.cursor(mdb.cursors.DictCursor)

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

    def __init__(self, *args):
        """
        """
        self.db = self.get_connection(*args)

    def get_connection(self, *args):
        """
        Parse the argument to Pymongo Client
        and return a collection object to connect to the db
        """
        db = args[0]
        c = pymongo.MongoClient()
        try:
            user = args[2]
            passw = args[3]
            db_auth = args[4]
            db_mech = args[5]
            confirmation = c[db].authenticate(user,
                                              passw,
                                              source=db_auth,
                                              mechanism=db_mech)
            logger.info('Authenticated: {}'.format(confirmation))
        except (IndexError, ValueError, TypeError):
            logger.info('Connection to the database without password and authentication')
        return c[db]

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

    parser = argparse.ArgumentParser(description='Get the tags from the mysql database')

    parser.add_argument('-c', '--config',
                        type=str,
                        default='config_dev.ini')

    args = parser.parse_args()
    config_file = '../config/'+args.config
    db_conn = connectDB(config_file)
    # set up access credentials
    config_value = configParser()
    config_value.read(config_file)

    DB_ACC_FILE = config_value['db_access'].get('DB_ACCESS_FILE'.lower(), None)
    access_value = configParser()
    access_value.read(DB_ACC_FILE)

    # Get the information about the db and the collections
    mongoDB_NAME = config_value['MongoDB'].get('DB_NAME'.lower(), None)

    mongoDB_JOB_COLL = config_value['MongoDB'].get('DB_JOB_COLLECTION'.lower(), None)
    mongoDB_TAG_COLL = config_value['MongoDB'].get('DB_TAG_COLLECTION'.lower(), None)

    # connect to the mongoDB
    mongoTag = mongoDB(mongoDB_NAME, mongoDB_JOB_COLL)

    # Create unique index on the JobId to avoid duplicating the records after launching the script
    # several time
    mongoTag.create_index(mongoDB_TAG_COLL, 'jobid', unique=True)

    # # MYSQL ACCESS # #
    mysql_host = access_value['MYSQL'].get('db_host', None)
    mysql_dbname = access_value['MYSQL'].get('db_name', None)
    mysql_username = access_value['MYSQL'].get('db_username', None)
    mysql_password= access_value['MYSQL'].get('db_password', None)

    # Connect to the mysql db
    mysqlConnection = mySQL(host=mysql_host, user=mysql_username, password=mysql_password, db=mysql_dbname)

    # Transferring the data from mysql to mongoDB
    for rows in mysqlConnection.search_final_classification():
        # print(rows)
        mongoTag.update_list_of_tags(mongoDB_TAG_COLL, rows)
    mongoTag.update_done(mongoDB_TAG_COLL)


if __name__ == "__main__":
    main()
