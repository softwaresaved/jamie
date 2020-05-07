# Default features for RSE jobs

from .feature import FeatureBase


def feature_union():
    """
    Pipeline to create a feature union.
    https://medium.com/bigdatarepublic/integrating-pandas-and-scikit-learn-with-pipelines-f70eb6183696
    """
    return FeatureUnion(n_jobs=1, transformer_list=[
                                        ('description', Pipeline([('selector', TextSelector('description')),
                                                        ('tfidf', TfidfVectorizer(sublinear_tf=True, norm='l2', ngram_range=(1, 2), stop_words='english'))
                                        ])),

                                        ('job_title', Pipeline([('selector',
                                                                   TextSelector('job_title')),
                                                        ('tfidf', TfidfVectorizer(sublinear_tf=True, norm='l2', ngram_range=(1, 2), stop_words='english'))
                                        ])),
                                       # ('num_terms_int', Pipeline([('selector', IntSelector('number_terms')),
                                       #                              ('scaler', StandardScaler()),
                                       #  ])),

                                        # ('num_terms_cat', Pipeline([('selector', SoftTermSelector('description')),
                                        # #                             ('encoder', MultiLabelBinarizer(classes=SEARCH_TERM_LIST)),
                                        #                             ('encoder', OneHotEncoder(n_values=len(SEARCH_TERM_LIST)))
                                        # ])),
                                        ('size_txt', Pipeline([('selector', LenSelector('description')),
                                            ('scaler', StandardScaler()),
                                        ])),

                                        # ('research_software', Pipeline([ ('selector', IntSelector('research_software')),
                                        #     # ('labeler', LabelEncoder()),
                                        #     ('encoder', OneHotEncoder())
                                        # ]))
                            # ])),
                        ])
    # X = transformer.fit_transform(df)
    # return X


def get_train_data(prediction_field):

    path_to_df = './data/training_set/training_set.csv'
    df = pd.read_csv(path_to_df)
    # df = find_words(df)
    # df = len_txt(df)
    # clean the text and try to find if there is a research software word in it
    df = check_if_research_software(df, cleaner)

    column_pred_field = '{}_tags'.format(prediction_field)
    # job_ids = df['jobid']
    y = prepare_labels(df, column=column_pred_field)
    features = feature_union()
    X = df[(df[column_pred_field] == '0') | (df[column_pred_field] == '1')][['description', 'job_title', 'research_software']]
    if len(X) == 0:  # Sometimes the labels are integers instead of strings
        X = df[(df[column_pred_field] == 0) | (df[column_pred_field] == 1)][['description', 'job_title', 'research_software']]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0, stratify=y)
    return X_train, X_test, y_train, y_test, features


if __name__ == "__main__":
    get_train_data('aggregate')
