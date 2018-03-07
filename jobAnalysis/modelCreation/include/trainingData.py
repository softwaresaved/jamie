#!/usr/bin/env python
# encoding: utf-8


"""
Training a classifier with the already classified jobs id
that are contained in mongodB.
Load a generator that contain the id the tag and the document
Split the data into two random dataset (the train and the test)
apply the classifier on the test
output the result
http://scikit-learn.org/stable/modules/cross_validation.html
"""


import numpy as np

from scipy import sparse
from sklearn.feature_extraction.text import TfidfTransformer

try:
    from include.logger import logger
except ModuleNotFoundError:
    from logger import logger
try:
    from include.getData import collectData
except ModuleNotFoundError:
    from getData import collectData
try:
    from include.configParser import ConfigParserPerso as configParser
except ModuleNotFoundError:
    from configParser import ConfigParserPerso as configParser

try:
    from include.vectorProcess import vectorProcess
except ModuleNotFoundError:
    from vectorProcess import vectorProcess

# ## GLOBAL VARIABLES  ###
# # To set up the variable on prod or dev for config file and level of debugging in the
# # stream_level
RUNNING = 'prod'

if RUNNING == 'dev':
    CONFIG_FILE = '../config_dev.ini'
    DEBUGGING='DEBUG'
elif RUNNING == 'prod':
    CONFIG_FILE = 'config.ini'
    DEBUGGING='INFO'

logger = logger(name='TrainingClass', stream_level=DEBUGGING)


class trainingData(vectorProcess):
    """
    """

    def __init__(self, training_set, **kwargs):
        """
        :params: training_set: generator containing the entire information on the training set
        """
        vectorProcess.__init__(self, **kwargs)
        self.vector = list()
        self.training_set = training_set

    @staticmethod
    def find_max(value, previous_value=0):
        """
        Function to return the max value
        """
        if value >= previous_value:
            return value
        else:
            return previous_value

    def get_ids(self):
        """
        Receive a list of ids and associated labels and return the
        founded documents.
        Transform the labels into a np.array. The output can be used
        directly into a classifier that use sklearn library
        :params: args[0]: str() to select the type of document to be returned
        :returns:
            :documents: list() of list() of founded document from the db
            :right_element: list() of the ids that were found in the db
            :np.array: of the labels associated to the tfidif
                object found in the db
        """
        list_jobsid = list()
        list_tag = list()
        list_doc = list()
        n = 0
        o = 0
        p = 0
        # max vector is to calculate the highest index value from the vector
        # to have the max value when applied to potential higher dimension vector
        self.max_vector = 0
        print('Collecting the training data')
        for jobid, tag, doc in self.training_set:
            # Some doc in the tag collection are not present in the vector collection
            if doc:
                if tag == 'Yes':
                    n += 1
                elif tag == 'None':
                    tag = 'No'
                    o += 1
                else:
                    print(tag)
                list_tag.append(tag)
                list_doc.append(doc)
                list_jobsid.append(jobid)

            else:
                p += 1
        logger.info('Number of Yes: {}'.format(n))
        logger.info('Number of No: {}'.format(o))
        logger.info('Number of not founded vectors: {}'.format(p))
        logger.info('Size of the founded trained dataset: {}'.format(len(list_doc)))
        logger.info('Max Vector: {}'.format(self.max_vector))
        return list_doc, list_jobsid, list_tag

    def transform_vector(self, data):
        """
        """
        output_vectors = list()
        for bag_of_words in data:
            vector = self.get_vector(bag_of_words)
            for x in vector:
                self.max_vector = self.find_max(x[0], self.max_vector)
            output_vectors.append(vector)
        return output_vectors

    def create_sparse_matrix(self, document, max_vector=None):
        """
        Transform the complete document of vector into a sparse matrix
        :params:
            :document: list of list of list of sparse vectors
            :max_vector: int() of the highest index value in the sparse vector
        :returns:
            :cx: sparse matrix build with the list of sparse vectors
        """
        # +1 because the index of the words starts at 0 so one less dimension
        try:
            cx = sparse.dok_matrix((len(document), max_vector+ 1))
        # In case max vector is none, need to find it inside the document
        except TypeError:
            max_vector = 0
            for vector in document:
                max_vector = self.find_max(vector[0], max_vector)
            # return back the same func() but with a max_vector value
            return self.create_sparse_matrix(document, max_vector)

        for row, doc in enumerate(document):
            for elt in doc:
                # if the document is one vector and not a list of several vector
                # the elt will be an int(). Solution is to transform that document
                # into a list of one document and relaunch the function.
                if isinstance(elt, int):
                    return self.create_sparse_matrix([document], max_vector)
                else:
                    try:
                        cx[row, elt[0]] = elt[1]
                    except TypeError:
                        raise(TypeError)
                    # that means the vector is higher than the max_vector
                    # no need to record it then
                    except IndexError:
                        pass

        return cx

    def transform_tfidf(self, data):
        """
        Use the tfidf instance from sklearn to apply tfidf to the spare matrix
        :params: sklearn.spare.matrix() containing all the vectorised document
        :return: X_tfidf, sklearn.dense.matrix() containing the tfidf transformed data
        """
        self.tfidf_transformer.fit(data)
        X_tfidf = self.tfidf_transformer.transform(data)
        # transform the matrix into a dense matrix
        X_tfidf.todense()
        return X_tfidf

    def standarise(self, data):
        """
        Standarise the vector or the matrix
        Use the tfidf instance from sklearn to apply tfidf to the spare matrix
        :params: sklearn.spare.matrix() containing all the vectorised document
        :return: X matrix with standarise data
        """
        return self.scaler.transform(data)


    def run(self, tfidf=True, standarise=False):
        """
        Wrapper for the class to launch and get everything at once
        """
        logger.info('Collect the data from the database')
        self.X, self.train_ids, self.y = self.get_ids()
        # transform the data into vectors
        self.X = self.transform_vector(self.X)
        logger.info('Fill the matrix with the data from the dataset')
        # Transform the vectors into a sparse_matrix
        self.X = self.create_sparse_matrix(self.X, self.max_vector)
        # Transform the spare matrix into tfidf
        # Instanciating the tfidif transformer with the LNorm (L2 by default)
        if tfidf is True:
            self.tfidf_transformer = TfidfTransformer(norm='l2')
            self.X = self.transform_tfidf(self.X)
        if standarise is True:
            self.scaler  = preprocessing.StandardScaler().fit(self.X)
            self.X = self.standarise(self.X)
        logger.info('Data collected and matrix built')
        # Transform the list of list_tag into np.array for the SVM classifier
        self.y = np.array(self.y)


def main():
    # INIT VALUES

    # ### CONNECTION TO DB ### #

    # set up access credentials
    # config_value = configParser().read_config(CONFIG_FILE)
    config_value = configParser()
    config_value.read(CONFIG_FILE)

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

    # Create the instance that connect to the db storing the training set
    mongoDB = collectData(mongoDB_NAME, mongoDB_USER,
                          mongoDB_PASS, mongoDB_AUTH_DB, mongoDB_AUTH_METH)

    # Get the generator from the database with the vector_clean


if __name__ == '__main__':
    main()
