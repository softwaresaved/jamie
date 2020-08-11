# Contributing

This document has general guidelines on contributing to Jamie and describes
areas where the code could be improved, as well as style guidelines.

[**Guidelines**](#guidelines) •
[**Testing**](#testing) •
[**Extending**](#extending) •
[**Dependencies**](#dependencies)

## Guidelines

First, install the development tools from the cloned repository directory:

    pip install .[dev,docs]

This will install several tools:

- [`flake8`](https://flake8.pycqa.org/en/latest/): Linter for Python code
- [`black`](https://black.readthedocs.io/en/stable/): Python code
  autoformatter, this ensures a consistent style
- [`pre-commit`](https://pre-commit.com/): Git pre-commit hooks which help fix
  code before committing. Install the git hooks by running `pre-commit install`
  in the repository once. This will trim trailing whitespaces, fix extra
  newlines at the end of the file and run `flake8` and `black` for linting and
  autoformatting.
- [`pytest`](https://docs.pytest.org): Run unit tests using `pytest tests`
- [`sphinx`](https://www.sphinx-doc.org/): Used to generate documentation from
- the `docs` folder. There is a
  Makefile in the docs folder which can generate documentation in various
  formats, such as HTML (`make html`).

Development on major features follows the [Github
flow](https://guides.github.com/introduction/flow/) model. There is a [project
changelog](CHANGELOG.md) following the [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/) guide to keep track of major
changes for each release.

There is continuous integration set up using Github Actions which will run some
unit tests and lint the code. If code linting fails, try running flake8 and
black locally to reproduce the CI error. Using pre-commit should fix linting
errors before committing locally.

The project uses a BSD 3-clause license, and is thus incompatible with GPL
code. **Licenses of added code (including dependencies) should be checked.**

## Testing

Code coverage is fairly low (less than 50%). Currently, there are partial unit
tests for the importer and parser. Some key areas where more testing would be
helpful are listed below.

- **Reproducibility**. In machine learning and data science applications such
  as Jamie, reproducibility is essential. While the code currently sets the
  scikit-learn `random_state` everywhere, there are no unit tests verifying
  reproducibility. Some issues with implementing reproducibility lies in the
  training time required (a few hours) which is prohibitively expensive for
  unit tests. This issue can be worked around by creating subsets of the
  training set to reduce the training time. Another issue is that the training
  data might be copyrighted which means that the test data cannot be stored in
  the same repository.
- **Scraping**. Since our test dataset is continuously being updated from a
  website, this can cause issues with scraping, such as when the website
  changes its HTML format. There should both be unit tests for scraping to
  ensure that data is being correctly cleaned, and also checks that new data
  follows the required format and has the required attributes for input to the
  machine learning pipeline.

  Particular care should be taken **not to break** existing cleaning and
  scraping, since that will make running the pipeline on old data to give
  different results and thus become unreproducible by the new code. Of course,
  this may be necessary if the scraping code has bugs, but this should be
  documented in the changelog.


Some of the larger tests, such as regression tests, can be run
[periodically](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions#onschedule)
using Github Actions.

## Extending

This section describes some common extensions and how to implement them.

### Adding a new featureset

Currently, there is only one [featureset](jamie/features/default.py) which
builds the features for the RSE job classification model. New featuresets could
be used to implement alternative job types such as data stewards, or try out
alternative features for existing job types.

1. Create a new submodule of features such as `jamie/features/new_features.py`.
1. Create a feature class, derived from [`FeatureBase`](jamie/features/base.py).
1. The base class has some parameters which check that particular columns are
   present in the data. It can also clean the data using `jamie.clean_text`.
1. Call `set_features()` and pass a list of features to be combined into a
   [FeatureUnion](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.FeatureUnion.html). This sets the `_features` attribute.
1. The main function to implement is `make_arrays()` which creates the feature
   matrix.
1. Add the new featureset to the `featuresets` dictionary in
   [`jamie.features`](jamie/features/__init__.py).
1. There are several helper functions such as feature transformers in the base
   feature module. In addition `FeatureBase` exposes common operations of the
   underlying features object such as `.fit_transform()` and
   `.train_test_split()` which derived classes get automatically.

### Adding a new graph

Jamie has a reporting interface with a number of graphs, such as those for
number of jobs and mean salary. New jobs can be added easily. All graphs are
created in two files [`jamie/reports.py`](jamie/reports.py) and
[`jamie/templates/script.js`](jamie/templates/script.js).

1. In reports, the main function to modify is the static method `metrics()`.
   This method takes a DataFrame parameter and returns a dictionary of metrics
   such as number of jobs and proportion of jobs classified as software jobs.
   This should be extended to add the metric of interest. Other functions such
   as `by_month()` and `by_year()` group the data by month and year
   respectively and use `metrics()` to create grouped metrics which are saved
   as JSON.
1. The file `script.js` contains all the graphs, which are displayed using the
   [MetricsGraphics](https://metricsgraphicsjs.org/) library. Creating a new
   graph is as simple as adding a new section to the file such as:

   ```javascript
   d3.json('by_month.json', function(data) {
       data = MG.convert.date(data, 'group');  // remove this for yearly data
       MG.data_graphic({
           title: "TITLE",
           data: data,
           width: 450,
           height: 250,
           area: false,
           color: "#2155a8",
           target: '#ID',
           x_accessor: 'group',
           y_accessor: 'YAXIS',
           brush: 'x'
       })
   })
   ```
   Here `ID` is the id of the HTML tag where the graph will be inserted by MetricsGraphics and `YAXIS` is the metric corresponding to the y-axis.

1. Add a new section for the graph to
   [`default_index.mustache`](jamie/templates/default_index.mustache). The
   graph will be inserted in a tag with `id=ID`.

## Dependencies

We should try to have as few dependencies as possible. Having dependencies
which are unmaintained could lead to security issues or incompatibilities
further down the line. This lists current dependencies, grouped by type and
their rationale:

- **Machine learning**: **scikit-learn** is the core dependency, while
  [**imbalanced-learn**](https://imbalanced-learn.org) is used for optional
  oversampling, **numpy** for general matrix manipulation, **pandas** for data
  manipulation. imbalanced-learn seems to be well maintained and has a
  [published article](https://imbalanced-learn.org/stable/about.html), while
  the others are standard well-known libraries.

  Licenses: New BSD (scikit-learn), BSD (numpy, pandas), MIT
  (imbalanced-learn).

- **Data visualization**: **matplotlib** is used to generate plots in the
  reports; these plots are deprecated as we use d3 for visualization now, but
  kept for possible inclusion in PDF reports. This is a well-known, widely used
  library.

  [**chevron**](https://github.com/noahmorrison/chevron) is used as a template
  engine to generate the report `index.html` file. The template engine uses the
  [mustache](http://mustache.github.io/) syntax. This library is not that
  well-known but essentially comprises two files, a renderer and tokenizer so
  should be easy to audit. Alternative mustache implementations or template
  engines could also be used instead.

  Licenses: [BSD-compatible](https://matplotlib.org/3.3.0/users/license.html) (matplotlib), MIT (chevron)

- **Scraping**: **requests** for fetching data over HTTP, **beautifulsoup4** for
  HTML parsing. **nltk** is used to clean the text data. All of these are well-known, widely used libraries. [**dateutil**](https://dateutil.readthedocs.io/) and [**datefinder**](https://github.com/akoumjian/datefinder) are used to parse dates from the text. dateutil is relatively widely used with many contributors, while datefinder is a smaller library that uses dateutil to find dates in text. datefinder has a few issues (such as not recognising ambiguous dates like 01/05/2000 properly before 0.7.2), but it is only used when no date can be found for the job.

  Licenses: Apache (requests, nltk), MIT (beautifulsoup4, datefinder), Apache +
  BSD (dateutil)

- **Database**: Connection to MongoDB is done via [**pymongo**](https://pymongo.readthedocs.io/) (Apache license).

- **CLI**: [**fire**](https://github.com/google/python-fire) is used to easily
  create the command line interface and
  [**tqdm**](https://tqdm.github.io) is used to display progress bars during
  training and prediction. Both of these libraries are well-maintained but can
  be removed if required, with fire being replaced by argparse and removing
  progress bars.

  Licenses: Apache (fire), MIT (tqdm)
