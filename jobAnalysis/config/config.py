#!/usr/bin/env python
# -*- coding: utf-8 -*-
author__= "Olivier Philippe"

"""
Different config information
"""


class Config:
    """
    Config class to be imported to set up
    options for others part of the project
    Can be imported in the different scripts as
    """
    # Variables to install and retrieve nltk files needed for the text cleaning
    NLTK_FILES = "./nltk_files/"
    LIST_PICKLES = ['punkt', 'maxent_treebank_pos_tagger', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
    NlTK_UPDATE = False

    # How the data are stored
    TYPE_DATA = 'db'

    # Maximum jobs downloaded to job.ac.uk in one go
    NUM_JOBS = 10000

    # Name of the database for mongodb
    DB_NAME = "jobsDB"

    # Name of the collection where all the information is stored
    DB_JOB_COLLECTION = "jobs"

    # Name of the collection where the tags given by BoB and stored in MySQL are copied in Mongodb
    DB_TAG_COLLECTION = "tags"

    # Name of the colleciton where all the information about the predictions are stored
    DB_PREDICTION_COLLECTION = "prediction"

    # Location of the access file where the credential for db are stored
    DB_ACCESS_FILE = None

    # Address of the MySQL DB where the tags from BoB are stored
    MYSQL_db_host = "127.0.0.1"

    # Port to connect to the MySQL DB
    MYSQL_port = None

    # Name of the collection containing the tags from BoB
    MYSQL_db_name = "classify"

    # Folder where the job files are stored
    INPUT_FOLDER = '/path/to/folder/'

    # Folder where to store the jobs for BoB classification
    SAMPLE_OUT_FOLDER = "/path/to/folder/"

    # Boolean to decide if it redo the modelling
    relaunch_model = False

    # Boolean to decide if it redo the prediction
    relaunch_prediction = False

    # Decide to record or not the prediction in the database
    record_prediction = True

    # Prediction field
    prediction_field = 'original'

    # Oversampling
    oversampling = False

    # Relaunch the include_in_study script
    relaunch_include = True

    # Number of k_fold for nested cross validation
    k_fold = 2

    # prediction model used to get the data
    prediction_to_recall = 'aggregate'

    # which metric to use for the gridsearch
    prediction_metric = 'precision'


class ConfigHome(Config):
    """
    Config for development, meaning the deployment on personal computer
    """
    INPUT_FOLDER = '/home/olivier/data/job_analysis/raw_jobs'

    DB_ACCESS_FILE = "/home/olivier/data/job_analysis/.access"

    MYSQL_port = 3306


class ConfigDevModel(ConfigHome):
    """
    Config for testing different modelling without modifying any existing db
    """
    INPUT_FOLDER = '/home/olivier/data/job_analysis/raw_jobs'

    k_fold = 5

    relaunch_model = False

    relaunch_include = False

    record_prediction = True

    oversampling = True

    prediction_field = 'aggregate'

    prediction_metric = 'balanced_accuracy'


class ConfigSoton(Config):
    """
    Config for deployment on Soton vm in rsg.soton.ac.uk
    """
    INPUT_FOLDER = "/disk/ssi-data0/home/deploy/jobs-data-etl/JobAdverts/JobsAcUk/"

    SAMPLE_OUT_FOLDER = "/disk/ssi-data0/home/deploy/jobs-data-etl/JobAdverts/Jobs4Bob"

    DB_ACCESS_FILE = "/disk/ssi-data0/home/deploy/jobs-data-etl/.access"

    k_fold = 5


class ConfigIridis(Config):

    """
    """
    relaunch_model = True

    record_prediction = False

    prediction_field = 'consensus'

    k_fold = 10

    oversampling = False


class ConfigIridis2(ConfigIridis):

    prediction_filed = 'consensus'

    oversampling = True


class ConfigIridis3(ConfigIridis):

    prediction_filed = 'aggregate'

    oversampling = False


class ConfigIridis4(ConfigIridis):

    prediction_filed = 'aggregate'

    oversampling = True
