# Base file for features
import numpy as np
import sklearn.model_selection as model_selection
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import LabelBinarizer
from ..text_clean import TextClean


class TextSelector(BaseEstimator, TransformerMixin):
    """Select a particular column from a pd.DataFrame.
    Like all transformers, you can use transform() to apply a transformation.

    Parameters
    ----------
    key : str
        Column to select
    """

    def __init__(self, key):
        self.key = key

    def transform(self, X):
        return X[self.key]

    def fit(self, X, y=None):
        return self


class CountTerm(BaseEstimator, TransformerMixin):
    """Add count of terms from a search term list

    Parameters
    ----------
    search_terms : list of str
        List of search terms
    """

    def __init__(self, search_terms):
        self.search_terms = search_terms

    def transform(self, X):
        return np.array(
            [len(set(i for i in self.search_terms if i in text)) for text in X],
            dtype=int,
            ndmin=2,
        ).T

    def fit(self, X, y=None):
        return self


class IntSelector(TextSelector):
    def transform(self, X):
        return X[[self.key]]


class LenSelector(IntSelector):
    """Length of a particular column from a pd.DataFrame.
    Like all transformers, you can use transform() to apply a transformation.

    Parameters
    ----------
    key : str
        Column to select
    """

    def len_txt(self, txt):
        return np.array([float(len(t)) for t in txt]).reshape(-1, 1)

    def transform(self, X):
        return self.len_txt(X[self.key])


class FeatureBase:
    """Base feature class

    Parameters
    ----------
    data : pd.DataFrame
        Data file to use
    require_columns : list of str
        List of required columns in DataFrame.
    clean_columns : list of str, optional
        List of columns to apply text cleaning to

    Raises
    ------
    ValueError
        If any of the required columns are missing
    """

    def __init__(self, data, require_columns, clean_columns=None):
        self.features = None
        self.data = data
        if any(f not in self.data for f in require_columns):
            raise ValueError("Missing one of required columns %r" % require_columns)
        if clean_columns:
            cleaner = TextClean()
            for tc in clean_columns:
                self.data[tc] = self.data[tc].apply(
                    lambda x: " ".join(cleaner.clean_text(x))
                )

    def set_features(self, features):
        "Set features using a FeatureUnion"
        self._features = FeatureUnion(n_jobs=1, transformer_list=features)
        return self

    def fit_transform(self, X, y=None):
        """Fit the features and transform with the final estimator.
        This calls the fit_transform() function of the underlying FeatureUnion object.
        The transformation pipeline converts from a CSV file to a numpy.ndarray.
        This method is usually called to create the training feature matrix
        from the CSV file.

        Parameters
        ----------
        X : pd.DataFrame
            Data to fit, usually from a CSV file
        y : array-like, optional
            This is ignored but kept for compatibility with other
            scikit-learn transformers

        Returns
        -------
        numpy.ndarray
            Feature matrix after applying pipeline
        """
        return self._features.fit_transform(X)

    def transform(self, X):
        """Transform X separately by each transformer in the FeatureUnion,
        concatenate results. This method is usually called to transform the
        test data X_test in a similar manner to X_train. Particularly for
        text transformation this preserves the vocabulary fitted from the
        training data.

        Parameters
        ----------
        X : pd.DataFrame
            Data to fit, usually from a CSV file

        Returns
        -------
        numpy.ndarray
            Feature matrix after applying transformation
        """
        return self._features.transform(X)

    def _prepare_labels(self, column):
        "Assign labels from column"
        y = self.data[(self.data[column] == "0") | (self.data[column] == "1")][column]
        if len(y) == 0:
            y = self.data[(self.data[column] == 0) | (self.data[column] == 1)][column]

        y = y.astype(np.float64)

        lb = LabelBinarizer()
        self.labels = lb.fit_transform(y).ravel()
        return self

    def make_arrays(self, prediction_field):
        """Build feature matrix. When the features class is initialized,
        it does not build the matrix before :meth:`make_arrays` is called.
        This does nothing in the base class, but is overloaded in the
        derived Feature classes. Typically it is the only function called
        from outside.

        Parameters
        ----------
        prediction_field : str
            Which column of the data to use as labels for prediction
        """
        pass

    def train_test_split(self, random_state, test_size=0.2):
        """Return different train test splits for ensemble by varying random_state.

        Parameters
        ----------
        random_state : int or RandomState
            Random state to use
        test_size : float, default=0.2
            Proportion of data to use for test

        Returns
        -------
        numpy.ndarray tuple
            Returns X_train, X_test, y_train, y_test
        """

        return model_selection.train_test_split(
            self.X,
            self.labels,
            test_size=test_size,
            random_state=random_state,
            stratify=self.labels,
        )
