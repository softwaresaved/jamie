#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os

import pandas as pd
import numpy as np

from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import KFold, cross_val_score, GridSearchCV, LeaveOneOut, StratifiedKFold, RandomizedSearchCV
from sklearn.naive_bayes import GaussianNB
from sklearn.model_selection import train_test_split
import sklearn.exceptions

import warnings
warnings.filterwarnings('ignore', category=sklearn.exceptions.UndefinedMetricWarning)


def record_result_csv(df, name_folds, folder):
    """
    Record the result of each outer_cv loop into a panda df and
    then record it into a csv.
    Before saving it checks if a similar csv file exists to append it instead
    of overwritting it.
    The name is based on the method to folds and just write the different models unders
    """
    filename = folder + 'average_scores_' + name_folds+ '.csv'
    if os.path.isfile(filename):
        df_to_append = pd.read_csv(filename, index_col=0)
        df_to_append = df_to_append.append(df)
        df_to_append.to_csv(filename)
    else:
        df.to_csv(filename)

def nested_cross_validation(X, y, feature_type, nbr_folds=2, folder='./outputs/'):
    """
    Dev version of the training instance
    Source: https://datascience.stackexchange.com/a/16856
    """

    print(y)
    # prepare models
    models = []
    # models.append(('LR', LogisticRegression()))
    # models.append(('LDA', LinearDiscriminantAnalysis()))
    # models.append(('KNN', KNeighborsClassifier()))
    # models.append(('CART', DecisionTreeClassifier()))
    # models.append(('NB', GaussianNB()))
    c_params = 10. ** np.arange(-3, 8)
    gamma_params = 10. ** np.arange(-5, 4)

    models = {'SVC': {'model': SVC(),
                      'param_grid': [{'C': c_params,
                                      'gamma': gamma_params,
                                      'kernel': ['rbf']},
                                      # 'class_weight': ['balanced', None]},
                                     {'C': c_params,
                                      'kernel': ['linear']}]
                      },
              'CART': {'model': DecisionTreeClassifier(),
                       'param_grid': [{'max_depth': range(3, 20)}]
                      }
              }

    # Create the outer_cv with 3 folds for estimating generalization error
    # outer_cv = StratifiedKFold(nbr_folds)
    # outer_csv = LeaveOneOut()
    # outer_cv  = LeaveOneOut(nbr_folds)
    # outer_cv = KFold(nbr_folds)

    # When trained a certain fold, doing the second cross-validation split to choose hyper parameters
    if isinstance(nbr_folds, int):
        # outer_cv = KFold(nbr_folds)
        outer_cv = StratifiedKFold(nbr_folds)
        # inner_cv = KFold(nbr_folds)
        inner_cv = StratifiedKFold(nbr_folds)
        name_outer_cv = 'kfold-{}'.format(nbr_folds)
    else:
        if nbr_folds.lower() == 'leaveoneout':
            inner_cv = LeaveOneOut()
            outer_cv = LeaveOneOut()
            nbr_folds = len(y)
            name_outer_cv = 'leaveoneout-{}'.format(str(nbr_folds))

    score_for_outer_cv = pd.DataFrame(index=range(len(models)),
                                      columns=['model', 'feature_type'])
    score_for_outer_cv['model'] = [name for name in models]

    columns_to_add = ['fold-{}'.format(int(i)+ 1) for i in range(nbr_folds)]
    score_for_outer_cv = score_for_outer_cv.reindex(columns=score_for_outer_cv.columns.tolist() + columns_to_add)

    average_scores_across_outer_folds_for_each_model = dict()
    # Get the average of the scores for the 10 folds
    for i, name in enumerate(models):

        model_opti_hyper_params = GridSearchCV(estimator=models[name]['model'],
                                               param_grid=models[name]['param_grid'],
                                               cv=inner_cv,
                                               scoring='f1',
                                               n_jobs=-1)

        # estimate generalization error on the K-fold splits of the data
        scores_across_outer_folds = cross_val_score(model_opti_hyper_params,
                                                    X, y,
                                                    cv=outer_cv,
                                                    scoring='f1',
                                                    n_jobs=-1)

        score_for_outer_cv.loc[score_for_outer_cv['model'] == name, ['feature_type']] = feature_type
        score_for_outer_cv.iloc[i, -nbr_folds:] = scores_across_outer_folds

        # get the mean MSE across each of outer_cv's K-folds
        average_scores_across_outer_folds_for_each_model[name] = np.mean(scores_across_outer_folds.mean())
        error_summary = 'Model: {name}\nMSE in the {nbr_folds} outer folds: {scores}.\nAverage error: {avg}'
        print(error_summary.format(name=name, nbr_folds=nbr_folds,
                                   scores=scores_across_outer_folds,
                                   avg=np.mean(scores_across_outer_folds)))
        print()



    record_result_csv(score_for_outer_cv, name_outer_cv, folder)
    print('Average score across the outer folds: ', average_scores_across_outer_folds_for_each_model)
    many_stars = '\n' + '*' * 100 + '\n'
    print(many_stars + 'Fitting the model on the training set Complete summary of the best model' + many_stars)

    best_model_name, best_model_avg_score = max(average_scores_across_outer_folds_for_each_model.items(),
                                                key=(lambda name_averagescore: name_averagescore[1]))

    # get the best model and its associated parameter grid
    best_model, best_model_params = models[best_model_name]['model'], models[best_model_name]['param_grid']

    # now we refit this best model on the whole dataset so that we can start
    # making predictions on other data, and now we have a reliable estimate of
    # this model's generalization error and we are confident this is the best model
    # among the ones we have tried
    final_model = GridSearchCV(best_model, best_model_params, cv=inner_cv, n_jobs=-1)
    final_model.fit(X, y)
    best_params = final_model.best_params_
    print(best_params)

    # return best_model, best_model_params
    return best_model_name, best_params, final_model


def adaboost(X, y):
    seed = 7
    num_trees = 100
    kfold = KFold(n_splits=10, random_state=seed)
    model = GradientBoostingClassifier(n_estimators=num_trees, random_state=seed)
    results = cross_val_score(model, X, y, cv=kfold)
    print(results.mean())
    # return print_score(model)

def models_pipeline():
    """
    Create a pipeline to test several models at once
    """
    models = Pipeline(['model':


def param_grid():
    """
    Change the hyperparameters for

