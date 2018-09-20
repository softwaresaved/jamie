#!/usr/bin/env python
# encoding: utf-8

"""
Generate data for all the different operations
"""
import os
import csv
import argparse
from datetime import timedelta

from bson import Code


import sys
from pathlib import Path
sys.path.append(str(Path('.').absolute().parent))

from common.logger import logger
from common.getConnection import connectDB

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

        self.first_id = self.get_record_ord(key='_id', order=1)
        self.last_id = self.get_record_ord(key='_id', order=-1)

        self.first_date = self.get_record_ord(key='placed_on', order=1)
        self.last_date = self.get_record_ord(key='placed_on', order=-1)

        self.days_range = self.create_days_range(self.first_date, self.last_date)
        self.all_keys = self.get_all_keys('jobs')

    def get_all_keys(self, collection):
        """
        Function to return all the distinct keys present in a collection
        :source: https://stackoverflow.com/a/48117846

        :params: coll str(): the collection to parse

        :return: list(): all the keys as str()
        """
        map_func = Code("function() { for (var key in this) { emit(key, null); } }")
        reduce_func = Code("function(key, stuff) { return null; }")
        result = self.db[collection].map_reduce(map_func, reduce_func, "myresults")
        return sorted(result.distinct('_id'))

    def get_record_ord(self, key, order):
        """
        Get the last record from the db before the run. Used to generated the report
        of the newly inserted jobs
        params:
            key str(): which key to query
            order int(): if -1 it give the last record, if 1 it gives the first record
        """
        try:
            return self.db_jobs.find({key: {'$exists': True}}, {key: True}).sort(key, order).limit(1)[0][key]
        except IndexError:  # In case of an empty collection
            return None

    def create_days_range(self, first_date, last_date):
        """
        Create a range of date per days for all the records.
        Search the placed_on key for the first and the last entry in the db and then delta them
        Loop throught the size of difference and add the day only to a list
        :params:
            fist_date datetime()
            last_date datetime()
        :return list(): ordered list of datetime object containing the date only
        """
        delta = last_date - first_date
        days_range = list()
        for i in range(delta.days + 1):
            day = first_date + timedelta(days=i)
            days_range.append(day.date())
        return sorted(days_range)

    @property
    def match_last_id(self):
        """
        Create a match query for the aggregate pipeline
        to restrict the result to the last record added
        before the current run
        """
        return [{'$match': {'_id': {'$gt': self.last_id}}}]

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
                                                     'count': {'$sum': 1}}}
                                         ]
            return get_enhanced_invalid_code

        def pipleline_invalid_code_without_salary():
            """
            Build the pipeline to query the entire database and get all the record split
            by TypeRole and if they have invalidCode or not. Give the count of each of
            these categories
            """
            get_enhanced_invalid_code = [{'$project': {'enhanced': 1,
                                                       'invalid_code': 1}},
                                         {'$project': {'enhanced': 1, 'invalid_code': 1,
                                                       "size_invalid_code": {'$cond': {'if': {'$gt': ['$invalid_code', None]},
                                                                                       'then': {'$size': '$invalid_code'},
                                                                                       'else': 0}
                                                                             }
                                                       }
                                          },
                                         {'$project': {'enhanced': 1, 'size_invalid_code': 1,
                                                       'invalid_code_salary': {'$cond': {"if": {'$or': [{'$gte': ['$size_invalid_code', 2]},
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
                                                     'count': {'$sum': 1}}}
                                         ]

            return get_enhanced_invalid_code

        if with_salary:
            pipeline = pipeline_invalid_code()
            type_data = 'invalid_code_with_salary'
        else:
            pipeline = pipleline_invalid_code_without_salary()
            type_data = 'invalid_code_without_salary'
        if from_begginning:
            pass
        else:
            pipeline = self.match_last_id + pipeline
        output = dict()
        for data in self.aggregate(pipeline):
            output.setdefault(data['_id']['enhanced'], {}).update({data['_id']['invalid_code']: data['count']})

        data_for_csv = list()
        for data in output:
            for item in output[data]:
                data_for_csv.append([data, item, output[data][item]])
        self.write_csv(header=['type of job html', 'type of code', 'count'],
                       result=data_for_csv,
                       name=type_data,
                       type_info='dataCollection')

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
        self.write_csv(header=['Type of invalid_code', 'count'],
                       result=data_for_csv,
                       name='count of invalid_code',
                       type_info='dataCollection')

    def get_unique_values(self, key, research_soft_only=False):
        """
        return unique value for the field specified by the key
        """
        set_unique = set()
        search = {key: {'$exists': True}}
        if research_soft_only is True:
            search['prediction'] = 1
        for data in self.db_jobs.find(search, {key: 1, '_id': 0}):
            set_unique.add(data[key].replace('\n', '\t').strip())
        with open('../../outputs/uniqueValue/{}.csv'.format(key), 'w') as f:
            for record in set_unique:
                try:
                    f.write('{}'.format(record))
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
            # Tranform the list of date (containing only one element) to a string
            try:
                to_add['date'] = d['_id']['date']
            except KeyError:
                to_add['date'] = 'None'

            list_to_append = [to_add[i] for i in header_csv]
            data_for_csv.append(list_to_append)
        self.write_csv(header_csv, data_for_csv, name_file, type_info='dataPrediction')

    def get_keys_per_day(self):
        """
        Output a csv file with the count for each keys
        """
        # Add a key total to get all the entry for one day
        list_to_parse = ['total']
        list_to_parse.extend(self.all_keys)

        # Remove the empty entry, jobid and _id
        list_to_parse.remove('')
        list_to_parse.remove('_id')
        list_to_parse.remove('jobid')
        # list_to_parse.remove('prediction')

        # Create a dictionary with all the days and set up an empty dict
        dict_key_with_date = {date_: dict() for date_ in self.days_range}

        # Populate each entry with
        for k in dict_key_with_date:
            for i in [0, 1, 'None']:
                dict_key_with_date[k][i] = {key: 0 for key in list_to_parse}

        # Add the Nan key

        dict_key_with_date['NaN'] = dict()
        for i in [0, 1, 'None']:
            dict_key_with_date['NaN'][i] = {key: 0 for key in list_to_parse}

        # Parse the db and return all the results
        for record in self.db_jobs.find({}):
            try:
                date_ = record['placed_on'].date()
            except KeyError:
                date_ = 'NaN'
            # Inc the total
            dict_key_with_date[date_][record['prediction']]['total'] +=1
            # Inc any keys that are present
            for k in record:
                try:
                    try:
                        if k not in record['invalid_code']:
                            dict_key_with_date[date_][record['prediction']][k] +=1
                    except KeyError:
                        dict_key_with_date[date_][record['prediction']][k]+=1
                except KeyError:
                    pass

        # Record the results
        filename = '{}dataCollection/presence_keys.csv'.format(self.report_csv_folder)
        with open(filename, "w") as f:
            group = ['date', 'prediction']
            fields = group + list_to_parse
            w = csv.DictWriter(f, fields)
            w.writeheader()
            for date_ in dict_key_with_date:
                date_record = dict_key_with_date[date_]
                for prediction in date_record:
                    row = date_record[prediction]
                    row['date'] = date_
                    row['prediction'] = prediction
                    w.writerow(row)

    def _get_average_per_day(self, key):

        pipeline = [{'$match': {'placed_on': {'$exists': True},
                                key: {'$exists': True},
                                'uk_university': {'$exists': True},
                                'prediction': {'$exists': True},
                                }
                     },
                    {'$group': {'_id': {'date': '$placed_on',
                                        'prediction': '$prediction'},
                                key: {'$avg': '${}'.format(key)}
                                }
                     }
                    ]

        for d in self.db_jobs.aggregate(pipeline):
            yield d

    def get_average_per_day(self, list_to_parse):
        """
        """
        if isinstance(list_to_parse, str):
            list_to_parse = [list_to_parse]

        for key in list_to_parse:
            header_csv = ['date', 'prediction', key]
            data_for_csv = list()
            name_file = 'average_{}'.format(key)
            for data in self._get_average_per_day(key):
                to_add = data['_id']
                to_add[key] = data[key]

                data_for_csv.append([to_add['date'], to_add['prediction'], to_add[key]])
            self.write_csv(header_csv, data_for_csv, name_file, type_info='dataAnalysis')

    def _get_sum_per_day(self, key):

        pipeline = [{'$match': {'placed_on': {'$exists': True},
                                'prediction': {'$exists': True},
                                'uk_university': {'$exists': True},
                                key: {'$exists': True}
                                }
                     },

                    {'$unwind': '${}'.format(key)},

                    {'$group': {'_id': {'date': '$placed_on',
                                        'prediction': '$prediction',
                                        key: '${}'.format(key)},
                                # 'total': {'$sum': '${}'.format(key)}
                                'count': {'$sum': 1}
                                }
                     }
                    ]
        for d in self.db_jobs.aggregate(pipeline):
            yield d

    def get_sum_per_day(self, list_to_parse):
        """
        """
        if isinstance(list_to_parse, str):
            list_to_parse = [list_to_parse]
        for key in list_to_parse:
            data_for_csv = list()
            header_csv = ['date', 'prediction', key, 'total']
            name_file = 'sum_{}'.format(key)
            for data in self._get_sum_per_day(key):
                to_add = data['_id']
                data_for_csv.append([to_add['date'], to_add['prediction'], to_add[key], data['count']])
            self.write_csv(header_csv, data_for_csv, name_file, 'dataAnalysis')

    def get_all_records(self):
        """
        """
        key_to_avoid = ['description', '_id', 'job_title']
        dict_key_to_avoid = {k: False for k in key_to_avoid}
        header = [i for i in self.all_keys if i not in key_to_avoid]
        data_for_csv = []
        for data in self.db_jobs.find({}, dict_key_to_avoid):
            data_for_csv.append(data)


        filename = os.path.join(self.report_csv_folder, 'dataCollection', 'all_records.csv')
        with open(filename, 'w') as f:
            w = csv.DictWriter(f, header)
            w.writeheader()
            for indict in data_for_csv:
                w.writerow(indict)

def main():
    """
    """
    # Parsing the config file name
    parser = argparse.ArgumentParser(description='Collect information from all the dataset and create csv file for being used in jupyter notebook without access to the databases')
    parser.add_argument('-c', '--config',
                        type=str,
                        default='config_dev.ini')
    args = parser.parse_args()
    config_file = '../config/' + args.config
    if config_file[-3:] != 'ini':
        config_file += '.ini'

    # Connect to the database
    db_conn = connectDB(config_file)
    db_jobs = db_conn['jobs']
    db_tag = db_conn['tags']
    db_prediction = db_conn['predictions']

    # Collect the different data
    generate_report = generateReport(db_conn, db_jobs, db_tag, db_prediction)

    logger.info('Invalid code with salary')
    logger.info(generate_report.get_invalid_code())

    logger.info('Invalid code without salary')
    generate_report.get_invalid_code(with_salary=False)

    logger.info('Count invalid code without salary')
    generate_report.count_invalid_codes()

    generate_report.get_keys_per_day()

    logger.info('Get the different average')
    for key in ['duration_ad_days']:
        generate_report.get_average_per_day(key)

    logger.info('Get the different sum')
    key_to_parse_for_sum_per_day = ['contract', 'hours', 'location', 'extra_location', 'subject_area', 'uk_university', 'type_role', 'uk_postcode']
    generate_report.get_sum_per_day(key_to_parse_for_sum_per_day)

    logger.info('Get the training set')
    generate_report.get_training_set()

    logger.info('Get the salary unique')
    generate_report.get_unique_values('salary')

    logger.info('Get the unique job title')
    generate_report.get_unique_values('job_title', research_soft_only=True)

    logger.info('Get the classifications')
    generate_report.get_classification()
    generate_report.get_all_records()


if __name__ == '__main__':
    main()
