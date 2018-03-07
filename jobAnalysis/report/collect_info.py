#!/usr/bin/env python
# encoding: utf-8

"""
Generate report for job2db.py run
"""
import os
import csv
import pymongo

from tabulate import tabulate
try:
    from include.logger import logger
except ModuleNotFoundError:
    from logger import logger

try:
    from include.configParser import ConfigParserPerso as configParser
except ModuleNotFoundError:
    from configParser import ConfigParserPerso as configParser

logger = logger(name='collect info', stream_level='DEBUG')


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

    def __init__(self, *args):
        """
        """
        self.db = args[0]
        self.db_tag = args[1]
        self.db_classification = args[2]
        self.report_csv_folder = './results/'
        self.last_id = self.get_last_id()

    def get_last_id(self):
        """
        Get the last record from the db before the run. Used to generated the report
        of the newly inserted jobs
        """
        try:
            return self.db.find({}, {'_id': True}).sort('_id', -1).limit(1)[0]['_id']
        except IndexError:  # In case of an empty collection
            return None

    @property
    def match_last_id(self):
        """
        Create a match query for the aggregate pipeline
        to restrict the result to the last record added
        before the current run
        """
        return [{'$match': {'_id': {'$gt': self.last_id}}}]

    def limiting_pipeline(self, pipeline, match):
        """
        Add a $match condition to a pipeline to filter the result to
        the record greater than the argument.
        return the appended pipeline
        """
        # match = self.build_match()
        return match + pipeline

    def aggregate(self, pipeline):
        """
        :params:
            :pipeline list(): pipeline to sent to the aggregate function in
                mongodb
        :return:
            dict() of the values

        """
        for info in self.db.aggregate(pipeline):
            yield info


    def write_csv(self, header, result, name):
        """
        """
        filename = os.path.join(self.report_csv_folder, '{}.csv'.format(name))
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in result:
                writer.writerow(row)



    def get_invalid_code(self, with_salary=True, from_begginning=True):

        def pipeline_invalid_code():
            """
            """
            get_enhanced_invalid_code = [{'$project': {'enhanced': 1,
                                                    'invalid_code': {'$cond': [{'$gt': ['$invalid_code', None]}, 'invalid_code', 'clean_entry']}}},
                                        {'$group': {'_id': {'enhanced': '$enhanced', 'invalid_code': '$invalid_code'},
                                                    'count': {'$sum':1}}}
                                        ]
            return get_enhanced_invalid_code

        def pipleline_invalid_code_without_salary():
            """
            Build the pipeline to query the entire database and get all the record split
            by TypeRole and if they have invalidCode or not. Give the count of each of
            these categories
            """
            get_enhanced_invalid_code = [{'$project': {'enhanced': 1,
                                                       'invalid_code': 1,}},
                                         {'$project': {'enhanced': 1, 'invalid_code': 1,
                                                       "size_invalid_code": {'$cond': {'if': {'$gt': ['$invalid_code', None]},
                                                                                       'then': {'$size': '$invalid_code'},
                                                                                       'else': 0}
                                                                            }
                                                      }
                                         },
                                         {'$project':{'enhanced': 1, 'size_invalid_code': 1,
                                                      'invalid_code_salary': {'$cond': {"if": {'$or': [
                                                                                                       {'$gte': ['$size_invalid_code', 2]},
                                                                                                       {'$and': [{'$eq': ['$size_invalid_code', 1]},
                                                                                                                 {'$eq': ['$invalid_code', 'salary']}
                                                                                                                ]
                                                                                                       }
                                                                                                      ]
                                                                                              },
                                                                              "then": 'invalid_code',
                                                                              "else": 'clean_entry'
                                                                                       }
                                                                             }
                                                     }
                                         },
                                         {'$group': {'_id': {'enhanced': '$enhanced', 'invalid_code': '$invalid_code_salary'},
                                                    'count': {'$sum':1}}}
                                        ]

            return get_enhanced_invalid_code

        if with_salary:
            pipeline = pipeline_invalid_code()
            type_data = 'invalid_code_with_salary'
        else:
            pipeline =  pipleline_invalid_code_without_salary()
            type_data = 'invalid_code_without_salary'
        if from_begginning:
            pass
        else:
            pipeline = self.limiting_pipeline(pipeline, self.match_last_id)
        output = dict()
        for data in self.aggregate(pipeline):
            output.setdefault(data['_id']['enhanced'], {}).update({data['_id']['invalid_code']: data['count']})

        data_for_csv = list()
        for data in output:
            for item in output[data]:
                data_for_csv.append([data, item, output[data][item]])
        self.write_csv(['type of job html', 'type of code',  'count'], data_for_csv, type_data)

        return output

    def count_invalid_codes(self):
        """
        """
        pipeline = [{'$match': {'invalid_code': {'$not': {'$size': 0}}}},
                    {'$unwind': '$invalid_code'},
                    {'$group': {'_id': '$invalid_code', 'count': {'$sum': 1}}},
                    {'$match': {'count': {'$gte': 1}}},
                    {'$sort': {'count': -1}},
                    {'$limit': 100}
                   ]
        data_for_csv = list()
        for data in self.aggregate(pipeline):
            data_for_csv.append([data['_id'], data['count']])
        self.write_csv(['Type of invalid_code', 'count'], data_for_csv, 'count of invalid_code')

    def get_list_posted_date(self):
        """
        """
        output_dict = dict()
        for data in self.db.find({}, {'placed_on': True}):
            try:
                output_dict[data['placed_on']] = output_dict.get(data['placed_on'], 0)+1
                # output_dict[data['placed_on'])] = output_dict.setdefault(data['placed_one'], 0)+1
            except KeyError:
                pass
        self.write_csv(['date posted', 'count'], [[k, output_dict[k]] for k in output_dict], 'date_posted')

    def get_salary(self):
        """
        """
        with open('./results/temp/salary.csv', 'w') as f:
            for data in self.db.find({'invalid_code': 'salary'}):
                try:
                    f.write('{}'.format(data['salary']))
                    f.write('\n')
                except KeyError:
                    pass

    def get_training_set(self):
        """
        Return the data about the training set
        """
        pipeline = [{'$group': {'_id': '$SoftwareJob', 'count': {'$sum': 1}}},
                    {'$sort': {'count': -1}}]
                    # {'$project': {'_id':  1, 'count': 1}}]

        data_for_csv = list()
        for data in self.db_tag.aggregate(pipeline):
            data_for_csv.append([data['_id'], data['count']])
        self.write_csv(['Type of classification', 'count'], data_for_csv, 'type_classification_bob')

    def get_classification(self):
        """
        Return data about the spread of the classification
        """
        pipeline=[{'$group': {'_id': {'folding': '$folding',
                                      'input_data': '$input_data',
                                      'input_field': '$input_field',
                                      'operation': '$operation',
                                      'prediction': '$prediction'},
                                      'count': {'$sum': 1}}}]

        data_for_csv = list()
        header_csv = ['folding', 'input_data', 'input_field', 'operation', 'prediction', 'count']
        for data in self.db_classification.aggregate(pipeline):
            to_add = data['_id']
            to_add['count'] = data['count']
            list_to_append = [to_add[i] for i in header_csv]
            data_for_csv.append(list_to_append)
        self.write_csv(header_csv, data_for_csv, 'predictions')

    def get_classification_per_details(self, key_to_get=None):
        """
        Get the classified jobs from the prediction db
        and match some field from the jobs db to aggregate by other
        type of information. Do it for each distinct algorithm and features
        """
        # First match every single combination
        pipeline_distinct =[{'$group': {'_id': {'folding': '$folding',
                                                'input_data': '$input_data',
                                                'input_field': '$input_field',
                                                'operation': '$operation'}}}]
        for data in self.db_classification.aggregate(pipeline_distinct):
            fields_to_match = data['_id']
            pipeline = [{'$match': {k: fields_to_match[k] for k in fields_to_match}},
                         {'$lookup': {'from': 'jobs',
                                      'localField': 'jobid',
                                      'foreignField': 'jobid',
                                      'as': 'results'}},
                        {'$unwind': '$results'},
                        {'$project': {'folding': 1,
                                      'input_data': 1,
                                      'input_field': 1,
                                      'model': 1,
                                      'operation': 1,
                                      'prediction': 1,
                                      # Split the date field with the space ('$split') then
                                      # return only the last element of that list (corresponding to the date
                                      # with '$slice'
                                      'year': {'$slice': [{'$split': ['$results.placed_on', ' ']}, -1] }}},
                         {'$group': {'_id': {'prediction': '$prediction',
                                             'model': '$model',
                                             'year': '$year'},
                                     'count': {'$sum': 1}}}
                        ]
            data_for_csv = list()
            name_file = 'prediction-per-year-{}'.format('-'.join(fields_to_match[k] for k in ['input_data', 'input_field', 'operation']))

            header_csv = ['year', 'model', 'prediction', 'count']
            for d in self.db_classification.aggregate(pipeline):
                to_add = d['_id']
                to_add['count'] = d['count']
                #Tranform the list of year (containing only one element) to a string
                try:
                    to_add['year'] = to_add['year'][0]
                except TypeError: # some none value due to impossibility to find the right date
                    to_add['year'] = 'Year not found'

                list_to_append = [to_add[i] for i in header_csv]
                data_for_csv.append(list_to_append)
            self.write_csv(header_csv, data_for_csv, name_file)


def main():
    """
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
        except (IndexError, ValueError, TypeError):
            logger.info('Connection to the database without password and authentication')
        return c[db][coll]

    # ### Get the variables NAMES from the config.ini file
    # config_value = configParser().read_config('./config.ini')
    config_value = configParser()
    config_value.read('./config_dev.ini')

    # Get the folder or the file where the input data are stored
    DB_ACC_FILE = config_value['db_access'].get('DB_ACCESS_FILE'.lower(), None)

    access_value = configParser()
    access_value.read(DB_ACC_FILE)
    # # MongoDB ACCESS # #
    mongoDB_USER = access_value['MongoDB'].get('db_username'.lower(), None)
    mongoDB_PASS = access_value['MongoDB'].get('DB_PASSWORD'.lower(), None)
    mongoDB_AUTH_DB = access_value['MongoDB'].get('DB_AUTH_DB'.lower(), None)
    mongoDB_AUTH_METH = access_value['MongoDB'].get('DB_AUTH_METHOD'.lower(), None)

    # Get the information about the db and the collections
    mongoDB_NAME = config_value['MongoDB'].get('DB_NAME'.lower(), None)
    mongoDB_JOB_COLL = config_value['MongoDB'].get('DB_JOB_COLLECTION'.lower(), None)
    mongoDB_TAG = config_value['MongoDB'].get('DB_TAG_COLLECTION'.lower(), None)
    mongoDB_PREDICTION= config_value['MongoDB'].get('DB_PREDICTION_COLLECTION'.lower(), None)

    # ### Init the processes #####

    # Connect to the database
    logger.info('Connection to the database')
    db_jobs = get_connection(mongoDB_NAME, mongoDB_JOB_COLL, mongoDB_USER,
                             mongoDB_PASS, mongoDB_AUTH_DB, mongoDB_AUTH_METH)
    db_tag = get_connection(mongoDB_NAME, mongoDB_TAG, mongoDB_USER,
                             mongoDB_PASS, mongoDB_AUTH_DB, mongoDB_AUTH_METH)

    db_prediction = get_connection(mongoDB_NAME,mongoDB_PREDICTION, mongoDB_USER,
                             mongoDB_PASS, mongoDB_AUTH_DB, mongoDB_AUTH_METH)
    generate_report = generateReport(db_jobs, db_tag, db_prediction)

    logger.info('Invalid code with salary')
    logger.info(generate_report.get_invalid_code())
    logger.info('Invalid code without salary')
    generate_report.get_invalid_code(with_salary=False)
    generate_report.count_invalid_codes()
    generate_report.get_list_posted_date()
    generate_report.get_training_set()
    # generate_report.get_salary()
    generate_report.get_classification()
    generate_report.get_classification_per_details()


if __name__ == '__main__':
    main()
