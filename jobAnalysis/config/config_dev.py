#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Config:
    def __init__(self):
        """
        """
        self.NLTK_FILES = 
        self.NLTK_FILES = "./nltk_files/"
        self.LIST_PICKLES = ['punkt','maxent_treebank_pos_tagger', 'stopwords', 'wordnet',
                             'averaged_perceptron_tagger']
        self.NlTK_UPDATE = False
        self.INPUT_FOLDER = '/home/olivier/data/job_analysis/dev_new_parser'
        self.TYPE_DATA = 'db'
        self.NUM_JOBS = 10000
        self.DB_ACCESS_FILE = "/home/olivier/data/job_analysis/.access"
        self.DB_NAME = "jobsDB"
        self.DB_JOB_COLLECTION = "jobs"
        self.DB_TAG_COLLECTION = "tags"
        self.DB_PREDICTION_COLLECTION = "prediction"
        self.MYSQL_db_host = 127.0.0.1
        self.MYSQL_db_name = "classify"
        self.SAMPLE_OUT_FOLDER = "/disk/ssi-data0/home/deploy/jobs-data-etl/JobAdverts/Jobs4Bob"
