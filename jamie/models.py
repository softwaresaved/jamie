#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import pickle
import pandas as pd
import numpy as np

from imblearn.pipeline import Pipeline
from imblearn.over_sampling import RandomOverSampler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (
    cross_val_score,
    GridSearchCV,
    LeaveOneOut,
    StratifiedKFold,
)

c_params = 10.0 ** np.arange(-3, 8)
gamma_params = 10.0 ** np.arange(-5, 4)
models = {
    "SVC": {
        "model": SVC(probability=True),
        "params": [
            {
                "clf__C": c_params,
                "clf__gamma": gamma_params,
                "clf__kernel": ["rbf"],
                "clf__class_weight": ["balanced", None],
            },
            {"clf__C": c_params, "clf__kernel": ["linear"]},
        ],
        "matrix": "sparse",
    },
    "Logreg": {
        "model": LogisticRegression(),
        "params": {
            "clf__penalty": ["l1", "l2"],
            "clf__C": np.logspace(-4, 4, 20),
            "clf__solver": ["liblinear"],
        },
        "matrix": "sparse",
    },
    "RandomForest": {
        "model": RandomForestClassifier(),
        "params": {
            "clf__n_estimators": list(range(10, 101, 10)),
            "clf__max_features": list(range(6, 32, 5)),
        },
        "matrix": "sparse",
    },
    "CART": {
        "model": DecisionTreeClassifier(),
        "params": [{"clf__max_depth": range(3, 20)}],
        "matrix": "sparse",
    },
    "Gradient Boosting": {
        "model": GradientBoostingClassifier(),
        "params": {
            "clf__learning_rate": [0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2],
            "clf__min_samples_split": (2, 21),
            "clf__min_samples_leaf": (1, 21),
            "clf__max_depth": [3, 5, 8],
            "clf__max_features": ["log2", "sqrt"],
            "clf__criterion": ["friedman_mse", "mae"],
            "clf__subsample": [0.5, 0.618, 0.8, 0.85, 0.9, 0.95, 1.0],
        },
        "matrix": "sparse",
    },
}


def nested_cross_validation(
    X, y, prediction_field, scoring_value, oversampling=False, nbr_folds=5
):
    """
    Dev version of the training instance
    Source: https://datascience.stackexchange.com/a/16856
    """

    # Get the models
    # When trained a certain fold, doing the second cross-validation split to choose hyper parameters
    if isinstance(nbr_folds, int):
        # outer_cv = KFold(nbr_folds)
        outer_cv = StratifiedKFold(nbr_folds)
        # inner_cv = KFold(nbr_folds)
        inner_cv = StratifiedKFold(nbr_folds)
        name_outer_cv = "kfold".format(nbr_folds)
    else:
        if nbr_folds.lower() == "leaveoneout":
            inner_cv = LeaveOneOut()
            outer_cv = LeaveOneOut()
            nbr_folds = len(y)
            name_outer_cv = "leaveoneout-{}".format(str(nbr_folds))

    # Creaging the dataframe for the different scores
    score_for_outer_cv = pd.DataFrame(index=range(len(models)), columns=["model"])
    score_for_outer_cv["model"] = [name for name in models]
    columns_to_add = ["fold-{}".format(int(i) + 1) for i in range(nbr_folds)]
    score_for_outer_cv = score_for_outer_cv.reindex(
        columns=score_for_outer_cv.columns.tolist() + columns_to_add
    )
    average_scores_across_outer_folds_for_each_model = dict()

    for i, name in enumerate(models):
        if oversampling is True:
            estimator = Pipeline(
                [("sampling", RandomOverSampler()), ("clf", models[name]["model"])]
            )
        else:
            estimator = Pipeline([("clf", models[name]["model"])])

        try:
            params = models[name]["params"]
        except KeyError:
            params = None
        if params:
            estimator = GridSearchCV(
                estimator,
                param_grid=params,
                cv=inner_cv,
                scoring=scoring_value,
                n_jobs=-1,
            )

        # estimate generalization error on the K-fold splits of the data
        # with joblib.parallel_backend('dask'):
        scores_across_outer_folds = cross_val_score(
            estimator, X, y, cv=outer_cv, scoring=scoring_value, n_jobs=-1
        )

        # score_for_outer_cv.loc[score_for_outer_cv['model'] == name, ['feature_type']] = feature_type
        score_for_outer_cv.iloc[i, -nbr_folds:] = scores_across_outer_folds
        #
        # get the mean MSE across each of outer_cv's K-folds
        average_scores_across_outer_folds_for_each_model[name] = np.mean(
            scores_across_outer_folds.mean()
        )
        error_summary = "Model: {name}\nMSE in the {nbr_folds} outer folds: {scores}.\nAverage error: {avg}"

        print(
            error_summary.format(
                name=name,
                nbr_folds=nbr_folds,
                scores=scores_across_outer_folds,
                avg=np.mean(scores_across_outer_folds),
            )
        )
        print()

    print(
        "Average score across the outer folds: ",
        average_scores_across_outer_folds_for_each_model,
    )
    many_stars = "\n" + "*" * 100 + "\n"
    print(
        many_stars
        + "Fitting the model on the training set Complete summary of the best model"
        + many_stars
    )

    best_model_name, best_model_avg_score = max(
        average_scores_across_outer_folds_for_each_model.items(),
        key=(lambda name_averagescore: name_averagescore[1]),
    )

    # get the best model and its associated parameter grid
    try:
        best_model, best_model_params = (
            models[best_model_name]["model"],
            models[best_model_name]["params"],
        )
    except KeyError:  # In case the model doesnt have parameters
        best_model, best_model_params = models[best_model_name]["model"], None
    print(models[best_model_name])

    # now we refit this best model on the whole dataset so that we can start
    # making predictions on other data, and now we have a reliable estimate of
    # this model's generalization error and we are confident this is the best model
    # among the ones we have tried
    estimator = Pipeline([("clf", models[best_model_name]["model"])])
    if best_model_params:
        params = models[best_model_name]["params"]
        final_model = GridSearchCV(estimator, params, cv=inner_cv, n_jobs=-1)
    else:
        final_model = GridSearchCV(estimator, cv=inner_cv, n_jobs=-1)
    final_model.fit(X, y)

    # Add the best model name in the best_model_params
    try:
        best_params = final_model.best_params_
    except AttributeError:
        best_params = None
    best_params["name"] = best_model_name

    return best_params, final_model, score_for_outer_cv


def train(training_snapshot):
    X, y = get_features(training_snapshot)
    best_params, final_model, score_for_outer_cv = nested_cross_validation(
        X, y, prediction_field, scorng_value)
    timestamp = current_date + 't' + training_snapshot + '_' + current_git_hash
    model_snapshot_folder = c['summary.snapshots'] / 'models' / timestamp
    if not model_snapshot_folder.exists():
        model_snapshot_folder.mkdir()
    with (model_snapshot_folder / 'model.pkl').open('wb') as fp:
        pickle.dump(final_model, fp)
    with (model_snapshot_folder / 'parameters.json').open('w') as fp:
        json.dump(best_params, fp)
    score_for_outer_cv.to_csv(model_snapshot_folder / 'score_outer_cv.csv', index=False)
