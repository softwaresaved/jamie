#!/usr/bin/env python
# encoding: utf-8

"""
Generate data for all the different operations
"""
import os
import csv
import pymongo
from bson import Code

import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from common.logger import logger
from common.getConnection import connectDB

# ## GLOBAL VARIABLES  ###
# # To set up the variable on prod or dev for config file and level of debugging in the
# # stream_level
RUNNING = 'dev'

if RUNNING == 'dev':
    CONFIG_FILE = '../config/config_dev.ini'
    DEBUGGING='DEBUG'
elif RUNNING == 'prod':
    CONFIG_FILE = '../config/config.ini'
    DEBUGGING='INFO'

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
        self.db_jobs = args[1]
        self.db_tag = args[2]
        self.db_predictions = args[3]
        self.report_csv_folder = '../../outputs/'
        self.last_id = self.get_last_id()

    def get_all_keys(self, collection):
        """
        Function to return all the distinct keys present in a collection
        :source: https://stackoverflow.com/a/48117846

        :params: coll str(): the collection to parse

        :return: list(): all the keys as str()
        """
        map = Code("function() { for (var key in this) { emit(key, null); } }")
        reduce = Code("function(key, stuff) { return null; }")
        result = self.db[collection].map_reduce(map, reduce, "myresults")
        return result.distinct('_id')

    def get_last_id(self):
        """
        Get the last record from the db before the run. Used to generated the report
        of the newly inserted jobs
        """
        try:
            return self.db_jobs.find({}, {'_id': True}).sort('_id', -1).limit(1)[0]['_id']
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
        for info in self.db_jobs.aggregate(pipeline):
            yield info

    def write_csv(self, header, result, name, type_info='dataCollection'):
        """
        """
        filename = os.path.join(self.report_csv_folder, type_info, '{}.csv'.format(name))
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in result:
                writer.writerow(row)

    def get_totals(self):

        pass

    def get_invalid_code(self, with_salary=True, from_begginning=True):

        def pipeline_invalid_code():
            """
            """
            get_enhanced_invalid_code = [{'$project': {'enhanced': 1,
                                                       'placed_on': 1,
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

    # def get_list_posted_date(self):
    #     """
    #     """
    #     output_dict = dict()
    #     for data in self.db.find({}, {'placed_on': True}):
    #         try:
    #             # date = get_month(data['placed_on'])
    #             date = data['placed_on']
    #             output_dict[date] = output_dict.get(date, 0)+1
    #             # output_dict[data['placed_on'])] = output_dict.setdefault(data['placed_one'], 0)+1
    #         except KeyError:
    #             pass
    #     self.write_csv(['date posted', 'count'], [[k, output_dict[k]] for k in output_dict], 'date_posted')

    def get_salary(self):
        """
        return unique value for the salary field
        """
        with open('../../outputs/salary.csv', 'w') as f:
            for data in self.db_jobs.distinct('salary', {'invalid_code': 'salary'}):
                try:
                    f.write('{}'.format(data.replace('\n', '\t').strip()))
                    f.write('\n')
                except KeyError:
                    pass

    def get_training_set(self):
        """
        Return the data about the training set
        """
        pipeline = [{'$group': {'_id': '$SoftwareJob', 'count': {'$sum': 1}}},
                    {'$sort': {'count': -1}}]

        data_for_csv = list()
        for data in self.db_tag.aggregate(pipeline):
            data_for_csv.append([data['_id'], data['count']])
        self.write_csv(['Type of classification', 'count'], data_for_csv, 'type_classification_bob', 'modelCreation')


    def get_classification(self, key_to_get=None):
        """
        Get the classified jobs from the prediction db
        and match some field from the jobs db to aggregate by other
        type of information. Do it for each distinct algorithm and features
        """
        pipeline = [{'$lookup': {'from': 'jobs',
                                 'localField': 'jobid',
                                 'foreignField': 'jobid',
                                 'as': 'results'
                                }},
                    {'$unwind': '$results'},
                    {'$project': {'model': 1,
                                  'prediction': 1,
                                  'date': '$results.placed_on'
                                 }},
                    {'$group': {'_id': {'prediction': '$prediction',
                                        'model': '$model',
                                        'date': '$date'},
                               'count': {'$sum': 1}
                               }}
                    ]
        data_for_csv = list()
        name_file = 'predictions'

        header_csv = ['date', 'model', 'prediction', 'count']
        for d in self.db_predictions.aggregate(pipeline):
            to_add = d['_id']
            to_add['count'] = d['count']
            #Tranform the list of date (containing only one element) to a string
            # try:
            to_add['date'] = d['_id']['date']
            #     # to_add['date'] = to_add['date'][0]
            # except (KeyError, TypeError): # some none value due to impossibility to find the right date
            #     to_add['date'] = 'date not found'

            list_to_append = [to_add[i] for i in header_csv]
            data_for_csv.append(list_to_append)
        self.write_csv(header_csv, data_for_csv, name_file, type_info='dataPrediction')

    def get_keys_per_day(self):
        """
        Output a csv file with the count for each keys
        """
        list_to_parse = self.get_all_keys('jobs')
        for k in list_to_parse:
            print(k)


def main():
    """
    """
    # Connect to the database
    db_conn = connectDB(CONFIG_FILE)
    db_jobs = db_conn['jobs']
    db_tag = db_conn['tags']
    db_prediction  = db_conn['predictions']
    generate_report = generateReport(db_conn, db_jobs, db_tag, db_prediction)
    generate_report.get_keys_per_day()
    # logger.info('Invalid code with salary')
    # logger.info(generate_report.get_invalid_code())
    # logger.info('Invalid code without salary')
    # generate_report.get_invalid_code(with_salary=False)
    # logger.info('Count invalid code without salary')
    # generate_report.count_invalid_codes()
    #
    # logger.info('Get the training set')
    # generate_report.get_training_set()
    # logger.info('Get the salary unique')
    # generate_report.get_salary()
    # logger.info('Get the classifications')
    # generate_report.get_classification()
    #

if __name__ == '__main__':
    main()
