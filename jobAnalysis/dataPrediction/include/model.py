#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os

import pandas as pd
import numpy as np


from sklearn.pipeline import Pipeline

from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.naive_bayes import GaussianNB



from sklearn.model_selection import KFold, cross_val_score, GridSearchCV, LeaveOneOut, StratifiedKFold, RandomizedSearchCV
from sklearn.model_selection import train_test_split

# import sklearn.exceptions
# import warnings
# warnings.filterwarnings('ignore', category=sklearn.exceptions.UndefinedMetricWarning)


def record_result_csv(df, name_folds, folder, prediction_field):
    """
    Record the result of each outer_cv loop into a panda df and
    then record it into a csv.
    Before saving it checks if a similar csv file exists to append it instead
    of overwritting it.
    The name is based on the method to folds and just write the different models unders
    """
    filename = folder + prediction_field + '/' + 'average_scores_' + name_folds+ '.csv'
    # if os.path.isfile(filename):
    #     df_to_append = pd.read_csv(filename, index_col=0)
    #     df_to_append = df_to_append.append(df)
    #     df_to_append.to_csv(filename)
    # else:
    df.to_csv(filename)

def nested_cross_validation(X, y, prediction_field, nbr_folds=5, folder='../../outputs/dataPrediction/prediction/'):
    """
    Dev version of the training instance
    Source: https://datascience.stackexchange.com/a/16856
    """
    c_params = 10. ** np.arange(-3, 8)
    gamma_params = 10. ** np.arange(-5, 4)

    models = {'SVC': {'model': SVC(probability=True),
                      'params': [{'C': c_params,
                                  'gamma': gamma_params,
                                  'kernel': ['rbf'],
                                  'class_weight': ['balanced', None]
                                 },
                                 {'C': c_params,
                                  'kernel': ['linear']
                                 }
                                ],
                      'matrix': 'sparse'
                     },

              'CART': {'model': DecisionTreeClassifier(),
                       'params': [{'max_depth': range(3, 20)}],
                       'matrix': 'sparse'
                      },

               'NB' : {'model': GaussianNB(),
                       'matrix': 'sparse'
                      },

              'Gradient Boosting': {'model': GradientBoostingClassifier(),

                                    'params': {
                                             "learning_rate": [0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2],
                                             "min_samples_split": np.linspace(0.1, 0.5, 12),
                                             "min_samples_leaf": np.linspace(0.1, 0.5, 12),
                                             "max_depth":[3,5,8],
                                             "max_features":["log2","sqrt"],
                                             "criterion": ["friedman_mse",  "mae"],
                                             "subsample":[0.5, 0.618, 0.8, 0.85, 0.9, 0.95, 1.0],
                                               },
                                    'matrix': 'sparse'
                                   }
               'RandomForest': {'model': RandomForestClassifier(),
                                'matrix': 'sparse'
                               },
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
        name_outer_cv = 'kfold'.format(nbr_folds)
    else:
        if nbr_folds.lower() == 'leaveoneout':
            inner_cv = LeaveOneOut()
            outer_cv = LeaveOneOut()
            nbr_folds = len(y)
            name_outer_cv = 'leaveoneout-{}'.format(str(nbr_folds))

    score_for_outer_cv = pd.DataFrame(index=range(len(models)),
                                      columns=['model'])
    score_for_outer_cv['model'] = [name for name in models]

    columns_to_add = ['fold-{}'.format(int(i)+ 1) for i in range(nbr_folds)]
    score_for_outer_cv = score_for_outer_cv.reindex(columns=score_for_outer_cv.columns.tolist() + columns_to_add)

    average_scores_across_outer_folds_for_each_model = dict()
    # Get the average of the scores for the {nbr_fold} folds
    for i, name in enumerate(models):
        estimator = models[name]['model']
        # estimator = Pipeline([('features', features), ('clf', model)])

        # print(estimator.get_params().keys())

        params = models[name]['params']
        # print(name, estimator, params)
        # if models[name]['matrix'] == 'dense':
        #     X = X.toarray()
        if params:

            estimator = GridSearchCV(estimator,
                                     param_grid=params,
                                     cv=inner_cv,
                                     scoring='precision_micro',
                                     n_jobs=-1)

        # estimate generalization error on the K-fold splits of the data
        scores_across_outer_folds = cross_val_score(estimator,
                                                    X, y,
                                                    cv=outer_cv,
                                                    scoring='precision_micro',
                                                    # scoring='precision',
                                                    n_jobs=-1)

        # score_for_outer_cv.loc[score_for_outer_cv['model'] == name, ['feature_type']] = feature_type
        score_for_outer_cv.iloc[i, -nbr_folds:] = scores_across_outer_folds
        #
        # get the mean MSE across each of outer_cv's K-folds
        average_scores_across_outer_folds_for_each_model[name] = np.mean(scores_across_outer_folds.mean())
        # error_summary = 'Model: {name}\nMSE in the {nbr_folds} outer folds: {scores}.\nAverage error: {avg}'

        # print(error_summary.format(name=name, nbr_folds=nbr_folds,
        #                            scores=scores_across_outer_folds,
        #                            avg=np.mean(scores_across_outer_folds)))
        # print()



    record_result_csv(score_for_outer_cv, name_outer_cv, folder, prediction_field)
    print('Average score across the outer folds: ', average_scores_across_outer_folds_for_each_model)
    many_stars = '\n' + '*' * 100 + '\n'
    print(many_stars + 'Fitting the model on the training set Complete summary of the best model' + many_stars)

    best_model_name, best_model_avg_score = max(average_scores_across_outer_folds_for_each_model.items(),
                                                key=(lambda name_averagescore: name_averagescore[1]))

    # get the best model and its associated parameter grid

    try:
        best_model, best_model_params = models[best_model_name]['model'], models[best_model_name]['params']
    except KeyError: ## In case the model doesnt have parameters
        best_model, best_model_params = models[best_model_name]['model'], None

    # now we refit this best model on the whole dataset so that we can start
    # making predictions on other data, and now we have a reliable estimate of
    # this model's generalization error and we are confident this is the best model
    # among the ones we have tried
    if best_model_params:
        final_model = GridSearchCV(best_model, best_model_params, cv=inner_cv, n_jobs=-1)
    else:
        final_model = GridSearchCV(best_model, cv=inner_cv, n_jobs=-1)
    try:
        final_model.fit(X, y)
    except ValueError:
        final_model.fit(X.toarray(), y)

    # Add the best model name in the best_model_params
    best_params = final_model.best_params_
    best_params['name'] = best_model_name
    # return best_model, best_model_params

    return final_model.best_params_, final_model


