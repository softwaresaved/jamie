#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import json
import pickle
import itertools
import pandas as pd
import numpy as np
import sklearn
from tqdm import tqdm
from box import Box
from pprint import pprint
from imblearn.pipeline import Pipeline
from imblearn.over_sampling import RandomOverSampler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (
    cross_validate,
    GridSearchCV,
    StratifiedKFold,
)
from .snapshots import TrainingSnapshotCollection
from .features import select_features
from .common.lib import isotime_snapshot, gitversion
from .logger import logger

logger = logger(name='models', stream_level='INFO')

SCORES = [
    "precision",
    "balanced_accuracy",
    "f1",
    "recall",
    "roc_auc"
]

def get_model(n):
    """Return model object corresponding to the named parameter.

    Parameters
    ----------
    n : str
        The name of the model

    Returns
    -------
    Model object
    """
    data = {
        "SVC": {
            "model": SVC,
            "params": {"probability": True}
        },
        "LogReg": {"model": LogisticRegression},
        "RandomForest": {"model": RandomForestClassifier},
        "CART": {"model": DecisionTreeClassifier},
        "GradientBoosting": {"model": GradientBoostingClassifier}
    }
    if n in data:
        if 'params' in data[n]:
            return data[n]['model'](**data[n]['params'])
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
        d = [int(x) for x in d[1:].split(":")]
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

def parse_model_description(model_description, models=None, random_state=100):
    """Parse models description. This function expands configuration values
    such as hyperparameter ranges from a string description to Python
    objects. The following interpositions are supported for parameter types:

    * ``=<start>:<stop>[:<step>]`` becomes **range** *(start,stop,step)*
    * ``=e<start>:<stop>[:<step>]`` becomes **np.logspace** *(start,stop,num)*

    Parameters
    ----------
    model_description : dict
        Dictionary representing models with their configuration
    models : Optional[List[str]]
        List of models to parse, by default parses all models
    random_state : int
        Random state to initialise seed, default: 100

    Returns
    -------
    dict
        Model description with parameters interposed using the above substitutions
    """

    k = dict()
    if models is None:
        models = model_description.keys()
    for n in model_description:
        if n not in models:
            continue
        print("Adding model:", n)
        k[n] = {"model": get_model(n), "matrix": model_description[n]["matrix"]}
        if isinstance(model_description[n]["params"], list):
            k[n]["params"] = []
            for p in model_description[n]["params"]:
                k[n]["params"].append({"clf__random_state": [random_state],
                                       **{c: parse_parameter_description(v)
                                          for c, v in p.items()}})
        else:  # is a dict
            k[n]["params"] = {"clf__random_state": [random_state],
                              **{c: parse_parameter_description(v)
                                 for c, v in model_description[n]["params"].items()}}
    return k


model_description = {
    "SVC": {
        "params": [
            {
                "clf__C": "=e-3:8:12",
                "clf__gamma": "=e-5:4:10",
                "clf__kernel": ["rbf"],
                "clf__class_weight": ["balanced", None],
            },
            {"clf__C": "=e-3:8:12", "clf__kernel": ["linear"]},
        ],
        "matrix": "sparse",
    },
    "LogReg": {
        "params": {
            "clf__penalty": ["l1", "l2"],
            "clf__C": "=e-4:4:20",
            "clf__solver": ["liblinear"],
        },
        "matrix": "sparse",
    },
    "RandomForest": {
        "params": {
            "clf__n_estimators": "=10:101:10",
            "clf__max_features": "=6:32:5",
        },
        "matrix": "sparse",
    },
    "CART": {
        "params": [{"clf__max_depth": "=3:20"}],
        "matrix": "sparse",
    },
    "GradientBoosting": {
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
    models, X, y, scoring_value, oversampling=False, nbr_folds=5, random_state=100
):
    """Perform nested cross validation and return best model. The set of
    models is defined in :mod:`jamie.models`. This function is generally
    not invoked directly, and is called through :func:`train`.

    Parameters
    ----------
    models : List[str]
        List of models to use, specify None for all models
    X : numpy.ndarray
        Feature matrix. This can be obtained by calling fit_transform() on a Features object
    y : numpy.ndarray
        Binary labels, should have the same number of rows as X
    scoring_value : score
        Which score type to use, same as in GridSearchCV
    oversampling : bool
        Whether to perform oversampling to balance the dataset (default: True)
    nbr_folds : int
        Number of folds for cross validation (default: 5)
    random_state : int
        Seed to initialise the random state (default: 100)

    Returns
    -------
    best_params : dict
        Best parameters for the final model
    final_model : model
        Final model
    score_for_outer_cv : pd.DataFrame
        Scores for outer cross validation for the various models
    """

    # Get the models
    # When trained a certain fold, doing the second cross-validation split to choose hyper parameters
    models = parse_model_description(model_description, models, random_state)
    # Use stratified folds as we have imbalanced dataset
    outer_cv = StratifiedKFold(nbr_folds)
    # Offset random_state by a fixed amount to create different shuffle
    inner_cv = StratifiedKFold(nbr_folds)

    # Creaging the dataframe for the different scores
    score_for_outer_cv = pd.DataFrame(index=range(len(models)), columns=["model"])
    score_for_outer_cv["model"] = [name for name in models]

    # Add nbr_folds for each score type
    columns_to_add = ["{}_{}".format(scoretype, int(i) + 1)
                      for scoretype, i in itertools.product(
                          SCORES, range(nbr_folds))] + \
        ["mean_" + scoretype for scoretype in SCORES]
    score_for_outer_cv = score_for_outer_cv.reindex(
        columns=score_for_outer_cv.columns.tolist() + columns_to_add
    )
    average_scores_across_outer_folds_for_each_model = dict()

    for i, name in enumerate(models):
        print("[{}] Begin training".format(name))
        if oversampling is True:
            print("Oversampling: ON")
            estimator = Pipeline(
                [("sampling", RandomOverSampler(random_state=random_state)),
                 ("clf", models[name]["model"])]
            )
        else:
            estimator = Pipeline([("clf", models[name]["model"])])

        try:
            params = models[name]["params"]
        except KeyError:
            params = None
        if params:
            print("[{}] GridSearchCV".format(name))
            estimator = GridSearchCV(
                estimator,
                param_grid=params,
                cv=inner_cv,
                scoring=scoring_value,
                n_jobs=-1,
            )

        # estimate generalization error on the K-fold splits of the data
        # with joblib.parallel_backend('dask'):
        print("[{}] Error estimation".format(name))
        scores_across_outer_folds = cross_validate(
            estimator, X, y, cv=outer_cv, scoring=SCORES, n_jobs=-1
        )

        # score_for_outer_cv.loc[score_for_outer_cv['model'] == name, ['feature_type']] = feature_type
        score_list = []
        for scoretype in SCORES:
            score_list.extend(scores_across_outer_folds["test_" + scoretype])
        # Add mean scores
        score_list.extend([scores_across_outer_folds["test_" + scoretype].mean()
                           for scoretype in SCORES])
        score_for_outer_cv.iloc[i, 1:] = score_list

        # Get the mean MSE across each of outer_cv's K-folds
        # While we report various scores, we only compare models
        # on scoring_value
        average_scores_across_outer_folds_for_each_model[name] = \
            scores_across_outer_folds["test_" + scoring_value].mean()
        print("[{}]   Fit time ".format(name), scores_across_outer_folds["fit_time"])
        print("[{}] Score time ".format(name), scores_across_outer_folds["score_time"])
        print()
        for scoretype in scores_across_outer_folds:
            if not scoretype.startswith("test_"):
                continue
            print("[{}]  Fold scores {:18s} [{}]".format(
                name, scoretype[5:],
                ", ".join("{:.5f}".format(s) for s in scores_across_outer_folds[scoretype])
            ))
        print()
        for scoretype in scores_across_outer_folds:
            if not scoretype.startswith("test_"):
                continue
            print("[{}]  Mean score  {:18s} {:.5f}".format(
                name, scoretype[5:], scores_across_outer_folds[scoretype].mean()))

        print()

    print(
        "Average score across the outer folds: ",
        average_scores_across_outer_folds_for_each_model,
    )
    logger.info("Fitting the model on the training set")

    best_model_name, best_model_avg_score = max(
        average_scores_across_outer_folds_for_each_model.items(),
        key=(lambda name_averagescore: name_averagescore[1]),
    )

    # get the best model and its associated parameter grid
    best_model_params = models[best_model_name].get("params", None)
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
        best_params = dict()
    best_params["name"] = best_model_name

    return best_params, final_model, score_for_outer_cv


def train(
    config, snapshot, featureset,
    models, prediction_field,
    oversampling, scoring,
    random_state=100
):
    """Train models, called when using ``jamie train`` and save model snapshots.

    Parameters
    ----------
    config : :class:`jamie.config.Config`
        Configuration object
    snapshot : str
        Training snapshot to use
    featureset : str
        Featureset to use
    models : Optional[List[str]]
        List of models to train on, by default all models are selected
    prediction_field : str
        Which column of the training set data to use for prediction.
    oversampling : bool
        Whether to oversample to form a balanced set, passed to :func:`nested_cross_validation`.
    scoring : str
        Scoring method to use for grid search, passed to :func:`nested_cross_validation`.
    random_state : int
        Seed to initialise the random state (default: 100)
    """
    filename = Box({'models': 'model.pkl', 'scores': 'scores.csv'})
    Features = select_features(featureset)
    timestamp = "_".join((featureset, isotime_snapshot(), gitversion()))
    model_snapshot_folder = config['common.snapshots'] / 'models' / timestamp
    metadata = {
        'snapshot': timestamp,
        'training': {
            'random_state': random_state,
            'training_snapshot': snapshot,
            'models': models,
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
    training_snapshots = TrainingSnapshotCollection(config['common.snapshots'])
    features = Features(training_snapshots[snapshot].data).make_arrays(prediction_field)
    logger.info("created features object")
    X_train = features.fit_transform(features.X)
    print("Data: {} jobs, {} features".format(*X_train.shape))
    logger.info("nested cross validation")
    best_model_params, final_model, average_scores = nested_cross_validation(
        models,
        X_train, features.labels, scoring,
        oversampling=oversampling,
        nbr_folds=config['model.k-fold'],
        random_state=random_state
    )

    # Create model snapshot folder if needed
    if not model_snapshot_folder.exists():
        model_snapshot_folder.mkdir(parents=True)

    # Run ensemble by fitting best_estimator from final_model to
    # 100 different train test splits
    estimator = copy.deepcopy(final_model.best_estimator_)
    for ensemble_state in tqdm(range(100), desc="Model ensemble"):
        X_train, _, y_train, _ = features.train_test_split(ensemble_state)
        X_train = features.fit_transform(X_train)
        estimator.fit(X_train, y_train)
        with (model_snapshot_folder /
                ('model_%d.pkl' % ensemble_state)).open('wb') as fp:
            pickle.dump(estimator, fp)
        with (model_snapshot_folder /
                ('features_%d.pkl' % ensemble_state)).open('wb') as fp:
            pickle.dump(features, fp)
    logger.info("saving models")
    # Save metadata, models list, models, parameters and scores
    metadata['best_parameters'] = best_model_params
    metadata['models'] = model_description
    with (model_snapshot_folder / 'metadata.json').open('w') as fp:
        json.dump(metadata, fp, indent=2, sort_keys=True)
    with (model_snapshot_folder / filename.models).open('wb') as fp:
        pickle.dump(final_model, fp)
    average_scores.to_csv(model_snapshot_folder / filename.scores, index=False)
