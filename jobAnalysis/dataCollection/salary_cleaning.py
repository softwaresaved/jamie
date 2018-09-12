
#!/usr/bin/env python
# encoding: utf-8

"""
Python script that Parse all the salary field and try
several rules to clean it with bettr results
Requirement:
    * config.ini file to collect information for the mongoDB connection
"""

import os
import re
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


logger = logger(name="salary_cleaning", stream_level="DEBUG")


list_per_year = ['per annum', 'pa', 'per year', 'p.a.', 'a year']

list_per_hour = ['per hour']

list_no_info = ['not specified', 'competitive salary', 'competitive salary and benefits']

def get_salary_field(*args, **kwargs):
    """
    Return the salary field from the mongodb
    """
    for salary in args[0].find({'salary': {'$exists': True}},
                               {'salary': 1}):
        yield (salary['salary'])


def get_number_pounds(*args, **kwargs):

    salary_fields = re.findall(r'£[0-9]?[0-9][0-9],[0-9][0-9][0-9]', args[0],
                                       flags=re.MULTILINE)
    return salary_fields


def check_for_number(s):

    return any(i.isdigit() for i in s)


def main():
    """
    """
    parser = argparse.ArgumentParser(
        description="Transform jobs ads stored in html file into the mongodb"
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
    nbr_job = db_jobs.count()

    nbr_improper_field = 0
    nbr_with_field = 0
    nbr_no_number_found = 0
    nbr_not_specified = 0
    nbr_proper_field = 0
    nbr_too_much_values = 0
    nbr_no_value_others = 0
    for salary in get_salary_field(db_jobs):
        nbr_with_field +=1
        salary = " ".join(salary.split())
        salary_pounds = get_number_pounds(salary)
        if len(salary_pounds) == 2 or len(salary_pounds) == 3:
            nbr_proper_field += 1
        else:
            nbr_improper_field += 1
            if len(salary_pounds) == 0:
                nbr_no_number_found +=1
                if check_for_number(salary) is False:
                    nbr_not_specified +=1
                else:
                    print(salary)
                    nbr_no_value_others +=1
            elif len(salary_pounds) >3:
                nbr_too_much_values +=1

    print('Total jobs in db: {}'.format(nbr_job))
    print('Total with salary field: {}'.format(nbr_with_field))
    print('Total with a proper salary field: {}'.format(nbr_proper_field))
    print('It means {}% have a correct salary_field'.format(nbr_proper_field/nbr_job*100))
    print('Total with an incorrect field: {}'.format(nbr_improper_field))
    print('Among theses there are:')
    print('\tNo value found: {}'.format(nbr_no_number_found))
    print('\tWhich are composed of:')
    print('\t\tNot specified or competitive: {}'.format(nbr_not_specified))
    print('\t\tNo value found for other reasons: {}'.format(nbr_no_value_others))
    print('\tToo much values: {}'.format(nbr_too_much_values))


if __name__ == "__main__":
    main()
