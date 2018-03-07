#!/usr/bin/env python
# encoding: utf-8

import os
import errno
import pymongo


from include.logger import logger
from include.textClean import textClean
from include.textTransform import textTransform
from include.textFeatures import ngramCreator
from include.vectorProcess import vectorProcess
# from include.tfidfTransformation import topicTransformation
from include.configParser import ConfigParserPerso as configParser


# ## GLOBAL VARIABLES  ###
# # To set up the variable on prod or dev for config file and level of debugging in the
# # stream_level
RUNNING = 'dev'

if RUNNING == 'dev':
    CONFIG_FILE = 'config_dev.ini'
    DEBUGGING='DEBUG'
elif RUNNING == 'prod':
    CONFIG_FILE = 'config.ini'
    DEBUGGING='INFO'

logger = logger(name='textTransformation', stream_level=DEBUGGING)


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


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


def create_index(coll, *args, unique=False):
    """
    Check if index exists and if not, creates it.
    MongoDB does not recreate it if already existing
    :params:
        coll: pymongo collection object
        *args: str() the key for the index
        unique: bool to set up the key as unique or not
    :return: None
    """
    if isinstance(*args, str):
        coll.create_index(*args, unique=unique)
    else:
        keys = [(k, pymongo.ASCENDING) for k in list(*args)]
        coll.create_index(keys, unique=unique)


def get_data(input_db, input_field, operation, input_data=None):
    """
    :params:
    :return: Generator with the record
    """

    if input_data:
        logger.debug('With input data: {}'.format(input_data))
        final_query = {'input_field': input_field, 'operation': input_data, 'feature.{}'.format(operation): {'$exists': False}}

    else:

        logger.debug('No input data')
        query = create_field_name(operation=operation, input_field=input_field, input_data=input_data)
        query = 'operation.{}'.format(query)
        if input_db._Collection__name == 'jobs':
            final_query = {input_field: {'$exists': True}, query: {'$exists': False}}
        else:
            final_query = {query: {'$exists': False}}

    logger.debug('Query the db: {}'.format(input_db))
    logger.debug('Final query: {}'.format(final_query))
    for document in input_db.find(final_query).batch_size(10):
        yield document


def create_field_name(**kwargs):
    """
    Get the type of operation and the data and return a join string
    """
    return '.'.join([value for v in ['input_field', 'operation', 'field_to_search', 'feature', 'input_data']
                    for value in (kwargs.get(v, None),)
                    if value is not None])


def update_txt_field(db, job_id, result=False, **kwargs):
    """
    Update the field txt_clean to T/F (boolean)
    :params:
        db: pymongo db object
        job_id: str() of the jobsId
        result: bool() to record in the db
        **kwargs: to get which key to record
    :return: None - Record in db
    """
    input_data = kwargs.get('input_data', None)
    if input_data:
        operation = kwargs.get('operation', None)

        final_field = 'feature.{}'.format(operation)
    else:
        field = create_field_name(**kwargs)
        final_field = 'operation.{}'.format(field)
    db.update({'JobId': job_id}, {'$set': {final_field: result}})


def update_vector_field(db, job_id, result, **kwargs):
    """
    """
    # field = create_field_name(**kwargs)
    # Add the vector to the field to create a vector embedded key in mongodb
    # otherwise raise pymongo.errors.WriteError
    # vector_field = 'vector.{}'.format(field)
    # db.update({'JobId': job_id, field: {'$exists': True}}, {'$set': {'vector': result}})
    data = kwargs['data']
    operation = kwargs['operation']
    db.update({'JobId': job_id, 'operation': operation,
               'input_field': data}, {'$set': {'vector': result}})


# FIXME Don't return False as stated by the docstring
def record_result(output_db, **kwargs):
    """
    Record the result into the database and skip if record already present
    :params:
        :output_db: mongoDB() object. Connection to a specfic collection
        :kwargs: Data to insert -- Expect:
            :job_id: str() of the jobsId
            :operation: str() to record the type of operation that has been applied
            :input_field: the type of data to record to know which field was transformed
            :data_to_record: the data to record itself
            :input_data: str() of the data of origin -- Optional
    :return: Bool() True if recorded, False if DuplicateKeyError
    """
    data_to_insert = {k: v for k, v in kwargs.items() if v is not None}
    try:
        output_db.insert(data_to_insert)
        return True
    except pymongo.errors.DuplicateKeyError:
        try:
            del kwargs['Description']
            print('Removed Description')
        except KeyError:
            pass
        # logger.debug('DuplicateKeyError in {}'.format(':'.join(str(v) for k, v in kwargs.items())))

        return True


def collecting_data(input_db, operation, input_field, input_data):
    # The different keys to acces to the data is because, depending on
    # which collection is queried, they are stored differently
    # mainly, db.jobs as a different scheme
    for data in get_data(input_db, input_field, operation, input_data):
        try:
            job_id = data['JobId']
        except KeyError:
            raise
        try:
            data = data['data']
        except KeyError:
            try:
                data = data[input_field]
            except KeyError:
                data = None
                logger.debug('No data in: {}:{}: {}'.format(operation, input_field, job_id))

        yield job_id, data


def record_vector(vector_process, data, output_db, vector_db, job_id, operation, input_field, input_data):
    """
    """
    data_to_record = vector_process.run(data)
    result = record_result(vector_db, JobId=job_id, operation=operation,
                           input_field=input_field, data=data_to_record,
                           input_data=input_data)
    update_vector_field(output_db, job_id, result=result, data=input_field, operation=operation)


def apply_transformation(func, input_db, output_db,
                         operation,
                         input_field,
                         input_data=None,
                         vector_db=None, vector_output_folder=None):
    """
    Apply a specific transformation to the entire dataset. Query only the records
    that do not have the key of previous changes recorded (key not present)
    Then modify the record in the input_db and record the result in the output_db
    Can accept different types of operation that need to be passed in this function.
    Optional: passing argument to vectorise and the result of the transformation will
    be vectorise at the same time and being recorded in separated db and files

    :params:
        func: passing the method object that return the data
        input_db: mongodbObject() connection to the collection where the input data
                  are stored int
        operation: str() that represent the operation done to record the appropriate
                        field in the input_db to avoid parsing the same data twice
        output_db: mongodbObject() connection to the collection where the output data
                   will be stored
        vector_db: mongodbObject() where the vector is going to be recorded (optional)
        vector_output_folder: str() to the folder where the vector dictionary is stored (optional)

    :return: None - Record results in db
    """
    def create_vectoriser():
        """
        """
        if vector_db and vector_output_folder:
            dict_name_str = create_field_name(input_field=input_field, operation=operation, input_data=input_data)
            return vectorProcess(dict_name=dict_name_str, result_dir=vector_output_folder)

    vector_process = create_vectoriser()
    n = 0
    o = 0
    if isinstance(input_data, str) is False:
        input_data = None
    for job_id, data in collecting_data(input_db, operation, input_field, input_data):
        n +=1
        result_bool = False
        if data:
            o +=1
            data_to_record = func(data)

            result_bool = record_result(output_db, JobId=job_id,
                                        operation=operation,
                                        input_field=input_field,
                                        data=data_to_record,
                                        input_data=input_data)
        update_txt_field(input_db, job_id, result=result_bool,
                         input_field=input_field, operation=operation, input_data=input_data)

        if vector_process and result_bool is True:
            record_vector(vector_process, data_to_record, output_db,
                          vector_db, job_id, operation, input_field, input_data)
        if n % 1000 ==0:
            logger.debug('Doing: {} -- {} -- With data: {} -- Without data: {}'.format(operation, n, o, n - o))
            if vector_process:
                logger.debug('Saving the dictionary')
                vector_process.save_dict()


def main():
    """ """
    # ### CONNECTION TO DB ### #

    # set up access credentials
    config_value = configParser()
    config_value.read(CONFIG_FILE)

    # INPUT_FOLDER = config_value['input'].get('INPUT_FOLDER'.lower(), None)

    # Get the folder or the file where the input data are stored
    input_data = config_value['input'].get('TYPE_DATA', None)

    # Get the output folder to store various result
    output_folder = config_value['output_file'].get('OUTPUT_FOLDER', None)
    if output_folder:
        make_sure_path_exists(output_folder)

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

    mongoDB_TXT_CLEAN_COLL = config_value['MongoDB'].get('DB_TXT_CLEAN_COLLECTION'.lower(), None)
    mongoDB_FEATURE_COLL = config_value['MongoDB'].get('DB_FEATURE_COLLECTION'.lower(), None)
    mongoDB_VECT_COLL = config_value['MongoDB'].get('DB_VECT_COLLECTION'.lower(), None)

    # Creating object for every collection
    db_jobs = get_connection(mongoDB_NAME, mongoDB_JOB_COLL, mongoDB_USER,
                             mongoDB_PASS, mongoDB_AUTH_DB, mongoDB_AUTH_METH)
    db_txt_clean = get_connection(mongoDB_NAME, mongoDB_TXT_CLEAN_COLL, mongoDB_USER,
                                  mongoDB_PASS, mongoDB_AUTH_DB, mongoDB_AUTH_METH)
    db_feature = get_connection(mongoDB_NAME, mongoDB_FEATURE_COLL, mongoDB_USER,
                                mongoDB_PASS, mongoDB_AUTH_DB, mongoDB_AUTH_METH)
    db_vect = get_connection(mongoDB_NAME, mongoDB_VECT_COLL, mongoDB_USER,
                             mongoDB_PASS, mongoDB_AUTH_DB, mongoDB_AUTH_METH)

    # Create the index for every collection
    create_index(db_txt_clean, ['JobId', 'input_field', 'operation', 'input_data'], unique=True)
    create_index(db_feature, ['JobId', 'input_field', 'operation', 'input_data'], unique=True)
    create_index(db_vect, ['JobId', 'input_field', 'operation', 'input_data'], unique=True)

    # get the type of data needed (need to be removed here for compatibility only
    if config_value['input'].get('TYPE_DATA', None) == 'db':
        data_jobs = db_jobs
    else:
        data_jobs = input_data
    logger.info('There are {} raw jobs'.format(data_jobs.count()))

    # ### Init the processes #####

    # list of tuples that has all the features to extracts
    list_of_features = list()

    # Cleaning text without stop words
    clean_process = textClean(remove_stop=False, **config_value).clean_text
    clean_in_db = data_jobs
    clean_out_db = db_txt_clean
    clean_type = 'clean'
    list_of_features.append((clean_process, clean_in_db, clean_out_db, clean_type))

    # # Cleaning text without stop words
    clean_process = textClean(remove_stop=True, **config_value).clean_text
    clean_in_db = data_jobs
    clean_out_db = db_txt_clean
    clean_type = 'clean_wo_stop'
    list_of_features.append((clean_process, clean_in_db, clean_out_db, clean_type))

    # STEM_LEM_POSTAG
    stem_process = textTransform(**config_value).transform_text
    stem_in_db = db_txt_clean
    stem_out_db = db_feature
    stem_type = 'lemmatise'
    stem_input_data = 'clean'
    list_of_features.append((stem_process, stem_in_db, stem_out_db, stem_type, stem_input_data))

    # # BIGRAM_CLEAN
    bigram_c_process = ngramCreator().run
    bigram_c_in_db = db_txt_clean
    bigram_c_out_db = db_feature
    bigram_c_type = '2gram'
    bigram_c_input_data = 'clean_wo_stop'
    list_of_features.append((bigram_c_process, bigram_c_in_db, bigram_c_out_db,
                             bigram_c_type, bigram_c_input_data))

    # ### Start the transformation ####
    input_field = 'Description'
    logger.debug('Doing the process for the field: {}'.format(input_field))
    for func, input_db, output_db, operation, *input_data in list_of_features:
        logger.info('Doing: {}'.format(operation))
        apply_transformation(func, input_db, output_db,
                             operation, input_field, *input_data,
                             vector_db=False, vector_output_folder=False)


if __name__ == '__main__':
    main()
