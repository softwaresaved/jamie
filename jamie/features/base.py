# Base file for features
import numpy as np
from slugify import slugify
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import FeatureUnion
from sklearn.preprocessing import LabelBinarizer
from ..common.textClean import textClean

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
    search_term_list : list of str
        List of search terms to use. This attribute may or may not be used
        depending on the particular featureset used
    require_columns : list of str
        List of required columns in DataFrame.

    Raises
    ------
    ValueError
        If any of the required columns are missing
    """

    def __init__(self, data, search_term_list, require_columns):
        self.search_term_list = search_term_list
        self.data = data
        if any(f not in self.data for f in require_columns):
            raise ValueError("Missing one of required columns %r" % require_columns)

    def _find_searchterms(self, row):
        return set(i for i in self.search_term_list if i in row)

    def _combine_features(self, features):
        "Combine features into a FeatureUnion"
        self.features = FeatureUnion(n_jobs=1, transformer_list=features)
        return self

    def add_searchterm(self, column):
        """Adds a search term column. This will add a column
        which will contain a list of search terms that have been found
        in that column.

        Parameters
        ----------
        column : str
            Column to apply search term flag to. This will create a new
            column called ``searchterm_<column>``

        Returns
        -------
        :class:`FeatureBase`
            Returns a copy of self with added column
        """
        self.data['searchterm_%s' % column] = self.data[column].apply(self._find_searchterms)
        return self

    def add_countterm(self, column):
        """Adds a countterm column. Similar to :meth:`add_searchterm`, except it adds
        a count of the number of unique search terms found in the column.

        Parameters
        ----------
        column : str
            Column to apply search term flag to. This will create a new
            column called ``countterm_<column>``

        Returns
        -------
        :class:`FeatureBase`
            Returns a copy of self with added column
        """

        if 'searchterm_%s' % column not in self.data:  # add searchterm field if not exists
            self.add_searchterm(column)
        self.data['nterm_%s' % column] = self.data['searchterm_%s' % column].apply(len)
        return self

    def add_textflag(self, search_for, in_column):
        """Adds a text flag column. This will add a binary column which
        contains 1 if a particular phrase is located in the text of
        a particular column

        Parameters
        ----------
        search_for : str
            Phrase to search for. The phrase is slugified before
            searching, i.e. converted to lowercase, and all spaces
            and special characters replaced by hyphens
        in_column : str
            Which column to search for phrase

        Returns
        -------
        :class:`FeatureBase`
            Returns a copy of self with added column
        """

        col = slugify(search_for).replace('-', '_')
        cleaner = textClean(remove_stop=False)
        self.data[col] = self.data[in_column].apply(
            lambda x: search_for in ' '.join(cleaner.clean_text(x)))
        return self

    def _prepare_labels(self, column):
        "Assign labels from column"
        y = self.data[(self.data[column] == '0') | (self.data[column] == '1')][column]
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
            self.X, self.labels, test_size=test_size,
            random_state=random_state, stratify=self.labels
        )
