#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import pickle
import pandas as pd
import numpy as np
import sklearn

from box import Box
from collections import namedtuple
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
from .snapshots import TrainingSnapshot
from .features import select_features
from .common.lib import isotime_snapshot, gitversion
from .config import Config
from .logger import logger

logger = logger(name='models', stream_level='INFO')
c_params = 10.0 ** np.arange(-3, 8)
gamma_params = 10.0 ** np.arange(-5, 4)

def get_model(n):
    data = {
        "SVC": {
            "model": SVC,
            "params": {"probability": True}
        },
        "LogReg": {"model": LogisticRegression},
        "RandomForest": {"model": RandomForestClassifier},
        "CART": {"model": DecisionTreeClassifier},
        "Gradient Boosting": {"model": GradientBoostingClassifier}
    }
    if n in data:
        if 'params' in data[n]:
            return data[n]['model'](**params)
        else:
            return data[n]['model']()
    else:
        return None

def parse_parameter_description(d):
    if not isinstance(d, str):
        return d
    if not d.startswith("="):  # start parsing on equals
        return d
    d = d[1:]  # drop the =
    if d.startswith("e"):  # logspace
        d = [int(x) for x in d.split(":")]
        if len(d) <= 3:
            return np.logspace(*d)  # start, stop, [num]
        else:
            raise ValueError("Parameter parsing error: " + d)
    else:  # normal range
        d = [int(x) for x in d.split(":")]
        if len(d) <= 3:
            return list(range(*d))  # start, stop, [num]
        else:
            raise ValueError("Parameter parsing error: " + d)

def parse_model_description(models):
    k = dict()
    for n in models:
        k[n] = {"model": get_model(n), "matrix": models[n]["matrix"]}
        if isinstance(models[n]["params"], list):
            k[n]["params"] = []
            for p in models[n]["params"]:
                k[n]["params"].append({
                    c: parse_parameter_description(v)
                    for c, v in p.items()})
        else:  # is a dict
            k[n]["params"] = {
                c: parse_parameter_description(v)
                for c, v in models[n]["params"].items()
            }
    return k


model_description = {
    # "SVC": {
    #     "model": SVC(probability=True),
    #     "params": [
    #         {
    #              "clf__C": c_params,
    #             "clf__gamma": gamma_params,
    #             "clf__kernel": ["rbf"],
    #             "clf__class_weight": ["balanced", None],
    #         },
    #         {"clf__C": c_params, "clf__kernel": ["linear"]},
    #     ],
    #     "matrix": "sparse",
    # },
    # "Logreg": {
    #     "model": LogisticRegression(),
    #     "params": {
    #         "clf__penalty": ["l1", "l2"],
    #         "clf__C": np.logspace(-4, 4, 20),
    #         "clf__solver": ["liblinear"],
    #     },
    #     "matrix": "sparse",
    # },
    # "RandomForest": {
    #     "model": RandomForestClassifier(),
    #     "params": {
    #         "clf__n_estimators": list(range(10, 101, 10)),
    #         "clf__max_features": list(range(6, 32, 5)),
    #     },
    #     "matrix": "sparse",
    # },
    "CART": {
        "params": [{"clf__max_depth": "=3:20"}],
        "matrix": "sparse",
    },
    # "Gradient Boosting": {
    #     "params": {
    #         "clf__learning_rate": [0.01, 0.025, 0.05, 0.075, 0.1, 0.15, 0.2],
    #         "clf__min_samples_split": (2, 21),
    #         "clf__min_samples_leaf": (1, 21),
    #         "clf__max_depth": [3, 5, 8],
    #         "clf__max_features": ["log2", "sqrt"],
    #         "clf__criterion": ["friedman_mse", "mae"],
    #         "clf__subsample": [0.5, 0.618, 0.8, 0.85, 0.9, 0.95, 1.0],
    #     },
    #     "matrix": "sparse",
    # },
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
    models = parse_model_description(model_description)
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
        _, best_model_params = (
            models[best_model_name]["model"],
            models[best_model_name]["params"],
        )
    except KeyError:  # In case the model doesnt have parameters
        _, best_model_params = models[best_model_name]["model"], None
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


def train(
    config, snapshot, featureset,
    prediction_field,
    oversampling, scoring
):
    filename = Box({'models': 'model.pkl', 'scores': 'scores.csv'})
    Features = select_features(featureset)
    timestamp = "_".join((featureset, isotime_snapshot(), gitversion()))
    metadata = {
        'snapshot': timestamp,
        'training': {
            'training_snapshot': snapshot,
            'featureset': featureset,
            'prediction_field': prediction_field,
            'oversampling': oversampling,
            'scoring': scoring
        },
        'pickle_protocol': pickle.DEFAULT_PROTOCOL,  # used for saving models
        'versions': {
            'pandas': pd.__version__,
            'numpy': np.__version__,
            'scikit-learn': sklearn.__version__  # different sklearn versions may not have compatible pickles
        },
        'config': config.as_dict(),
        'data': {
            'models': filename.models,
            'scores': filename.scores
        }
    }
    logger.info("model-snapshot %s", timestamp)
    training_snapshots = TrainingSnapshot(config['common.snapshots'])
    feature_data = Features(training_snapshots[snapshot]).make_arrays(prediction_field)
    logger.info("created features object")
    X_train = feature_data.features.fit_transform(feature_data.X_train)
    # X_test = feature_data.features.transform(feature_data.X_test)
    logger.info("nested cross validation")
    best_model_params, final_model, average_scores = nested_cross_validation(
        X_train, feature_data.y_train,
        prediction_field, scoring,
        oversampling=config['model.oversampling'],
        nbr_folds=config['model.k-fold'])
    # y_pred = final_model.predict(X_test)
    # y_proba = final_model.predict_proba(X_test)
    logger.info("saving models")
    model_snapshot_folder = config['common.snapshots'] / 'models' / timestamp
    # Save metadata, models list, models, parameters and scores
    if not model_snapshot_folder.exists():
        model_snapshot_folder.mkdir(parents=True)
    metadata['best_parameters'] = best_model_params
    metadata['models'] = model_description
    with (model_snapshot_folder / 'metadata.json').open('w') as fp:
        json.dump(metadata, fp, indent=2, sort_keys=True)
    with (model_snapshot_folder / filename.models).open('wb') as fp:
        pickle.dump(final_model, fp)
    average_scores.to_csv(model_snapshot_folder / filename.scores, index=False)

