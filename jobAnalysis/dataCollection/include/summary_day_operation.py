#!/usr/bin/env python
# encoding: utf-8

"""
Generate report for job2db.py run
"""
import csv
import pymongo

from tabulate import tabulate
from common.logger import logger

from common.configParser import configParserPerso as configParser

logger = logger(name='summary_day_operation', stream_level='DEBUG')


class generateReport:
    """
    Class to create a complete report at the end of the job2db.py process
    It parse the db to collect information about the total record, and the
    type of records that have been stored before the new run.
    Then receive the evolution of the data collection and insertion and
    output them at the end.
    It also output the type of records stored during the run and the last information
    Use tabulate to format the different tables
    """

    def __init__(self, db):
        """
        """
        self.db = db
        self.nb_processed_job = 0
        self.nb_inserted_job = 0
        self.nb_duplicated_job = 0
        self.report_csv_filename = '../../../outputs/dataCollection_job2db.csv'
        self.nb_mongo_error_job = 0
        self.last_id = self.get_last_id()
        self.pipeline = self.build_pipeline()
        self.limited_pipeline = self.limited_pipeline()

    def get_last_id(self):
        """
        Get the last record from the db before the run. Used to generated the report
        of the newly inserted jobs
        """
        try:
            return self.db.find({}, {'_id': True}).sort('_id', -1).limit(1)[0]['_id']
        except IndexError:  # In case of an empty collection
            return None

    def build_pipeline(self):
        """
        Build the pipeline to query the entire database and get all the record split
        by TypeRole and if they have invalidCode or not. Give the count of each of
        these categories
        """
        # Use $gt instead of $eq because $eq return only false
        # No idea why but tip here: http://stackoverflow.com/questions/25497150/mongodb-aggregate-by-field-exists
        pipeline = [{'$unwind': '$TypeRole'},
                    {'$project': {'TypeRole': 1,
                                  'BoolCode': {"$cond": [{"$gt": ["$InvalidCode", None]}, True, False]}}},
                    {'$group': {'_id': {'TypeRole': '$TypeRole',
                                        'InvalidCode': '$BoolCode'},
                                'count': {'$sum': 1}}}
                    ]
        return pipeline

    def limited_pipeline(self):
        """
        Add a $match condition to a pipeline to filter the result to
        the record greater than the argument.
        return the appended pipeline
        """
        match = self.build_match()
        return match + self.pipeline

    def build_match(self):
        """
        Create a match query for the aggregate pipeline
        to restrict the result to the last record added
        before the current run
        """
        return [{'$match': {'_id': {'$gt': self.last_id}}}]

    def aggregate(self, pipeline):
        """
        """
        def transform_result(result):
            """
            Create the element to output a table with the results from the aggregate
            :params: result - Dictionary containing result from aggregate()
            """
            # return [[k, result[k][False], result[k][True]] for k in sorted(result)]
            output = list()
            for k in sorted(result):
                sublist = [k]
                total = 0
                for i in [False, True]:
                    try:
                        to_add = result[k][i]
                    except KeyError:
                        to_add = 0
                    sublist.append(to_add)
                    total += to_add
                sublist.append(total)
                output.append(sublist)
            return output

        output = dict()
        for info in self.db.aggregate(pipeline):
            output.setdefault(info['_id']['TypeRole'], {}).update({info['_id']['InvalidCode']: info['count']})

        # Building the total based on the structure of transform_result() and create a list
        # for the tabulate function
        # TODO Not implemented yet
        # total = list()
        # total.append('Total')
        # total.append(sum(l for i in output for l in i[1]))
        # total.append(sum(l for i in output for l in i[2]))
        return transform_result(output)

    def output_table(self, *args, formatting='psql'):
        """
        Create the table from the data input and use tabulate to output
        a clean table on the terminal and on cron job
        :params:
            :args[0]: the header of the table (int)
            :args[1]: the table
            :args[2]: the headers
            :formatting: the tabulate formatting - default 'psql'
        :output
            :the string to format with logger
        """
        # Get the \n to clean the output  -- otherwise the table is pushed on the right
        return ('\n\n+--- {} ---+\n{}\n'.format(args[0], tabulate(args[1], headers=args[2], tablefmt=formatting)))

    def get_current(self):
        """
        """
        result = self.aggregate(self.limited_pipeline)
        headers = ['Type Role', 'Clean Result', 'Wrong Code', 'Total']
        title = 'NEW JOBS INSERTED'
        return self.output_table(title, result, headers)

    def get_total(self):
        """
        """
        result = self.aggregate(self.pipeline)
        headers = ['Type Role', 'Clean Result', 'Wrong Code', 'Total']
        title = 'TOTAL RECORDS'
        return self.output_table(title, result, headers)

    def get_summary(self):
        """
        """
        self.headers = ['', 'Count']
        self.title = 'Result of job2db'
        self.result = [['Job processed', self.nb_processed_job],
                       ['Job inserted', self.nb_inserted_job],
                       ['Duplicated ids', self.nb_duplicated_job],
                       ['Mongodb Errors', self.nb_mongo_error_job]]
        return self.output_table(self.title, self.result, self.headers)

    def write_csv(self):
        """
        """
        with open(self.report_csv_filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)
            for l in self.result:
                writer.writerow(l)


def main():
    """
    Test purpose only
    """
    def get_connection(*args):
        """
        Parse the argument to Pymongo Client
        and return a collection object to connect to the db
        """
        db = args[0]
        coll = args[1]
        c = pymongo.MongoClient()
        try:
            user = args[2]
            passw = args[3]
            db_auth = args[4]
            db_mech = args[5]
            confirmation = c[db].authenticate(user, passw, source=db_auth, mechanism=db_mech)
            logger.info('Authenticated: {}'.format(confirmation))
        except (IndexError, ValueError):
            logger.info('Connection to the database without password and authentication')
        return c[db][coll]

    # ### Get the variables NAMES from the config.ini file
    # config_value = configParser().read_config('./config.ini')
    config_value = configParser().read_config('../config_dev.ini')

    # Get the folder or the file where the input data are stored
    DB_ACC_FILE = config_value.get('DB_ACCESS_FILE'.lower(), None)

    access_value = configParser().read_config(DB_ACC_FILE)

    DB_NAME = access_value.get('DB_NAME'.lower(), None)
    DB_COLL = access_value.get('DB_COLLECTION'.lower(), None)
    DB_USER = access_value.get('DB_USERNAME'.lower(), None)
    DB_PASS = access_value.get('DB_PASSWORD'.lower(), None)
    DB_AUTH_DB = access_value.get('DB_AUTH_DB'.lower(), None)
    DB_AUTH_METH = access_value.get('DB_AUTH_METHOD'.lower(), None)
    # Connect to the database
    logger.info('Connection to the database')
    db_jobs = get_connection(DB_NAME, DB_COLL, DB_USER, DB_PASS, DB_AUTH_DB, DB_AUTH_METH)
    generate_report = generateReport(db_jobs)
    logger.info(generate_report.get_summary())
    logger.info(generate_report.get_current())
    logger.info(generate_report.get_total())


if __name__ == '__main__':
    main()
