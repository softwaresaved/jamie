# Default features for RSE jobs
from sklearn.feature_extraction.text import TfidfVectorizer
from imblearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from .base import FeatureBase, TextSelector, LenSelector
from sklearn.model_selection import train_test_split

SEARCH_TERM_LIST = [
    'algorithm',
    'big data',
    'beautifulsoup',
    'code',
    'computation',
    'computational',
    'computed',
    'computer',
    'data analysis',
    'data base',
    'database',
    'excel',
    'fortran',
    'geographic information science',
    'geographic information systems',
    'gis',
    'git',
    'github',
    'graphics',
    'high performance computing',
    'hpc',
    'imagej',
    'implemented in',
    'in silico',
    'matlab',
    'matplotlib',
    'numpy',
    'nvivo',
    'open source',
    'open-source',
    'pipeline',
    'python',
    'quantitative',
    'regression',
    'r language',
    'in r',
    'scrapy',
    'scipy',
    'simulated',
    'simulation',
    'software',
    'spss',
    'sqlalchemy',
    'stata',
    'statistical'
    'supercomputing',
    'visualisation',
    'visualization',
    'Rcpp',
    'ggplot2',
    'plyr',
    'stringr',
    'reshape2',
    'RColorBrewer',
    'workflow',
    'wxpython'
]

class RSEFeatures(FeatureBase):
    def __init__(self, data):
        super().__init__(data, SEARCH_TERM_LIST, require_columns=[
            'description', 'job_title'])
        self.combine_features([
            ('description', Pipeline([('selector', TextSelector('description')),
                                      ('tfidf', TfidfVectorizer(sublinear_tf=True, norm='l2',
                                       ngram_range=(1, 2), stop_words='english'))])),
            ('job_title', Pipeline([('selector', TextSelector('job_title')),
                                    ('tfidf', TfidfVectorizer(sublinear_tf=True, norm='l2',
                                     ngram_range=(1, 2), stop_words='english'))])),
            ('size_txt', Pipeline([('selector', LenSelector('description')),
                                   ('scaler', StandardScaler())])),
        ])

    def make_arrays(self, prediction_field):
        self.prepare_labels(prediction_field)
        self.data[prediction_field] = self.data[prediction_field].astype(str)
        self.add_textflag(search_for='research software', in_column='description')
        self.X = self.data[(self.data[prediction_field] == '0') |
                           (self.data[prediction_field] == '1')][
            ['description', 'job_title', 'research_software']]
        self.X_train, self.X_test, self.y_train, self.y_test = \
            train_test_split(self.X, self.labels, test_size=0.2,
                             random_state=0, stratify=self.labels)


if __name__ == "__main__":
    print(__file__)
