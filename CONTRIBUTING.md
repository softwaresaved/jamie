# Contributing

This document has general guidelines on contributing to Jamie and describes
areas where the code could be improved, as well as style guidelines.

## Guidelines

First, install the development tools from the cloned repository directory:

    pip install .[dev,docs]

This will install several tools:

- [`flake8`](https://flake8.pycqa.org/en/latest/): Linter for Python code
- [`black`](https://black.readthedocs.io/en/stable/): Python code
  autoformatter, this ensures a consistent style
- [`pre-commit`](https://pre-commit.com/): Git pre-commit hooks which help fix
  code before committing. To install the git hooks, run `pre-commit install` in
  the repository once. This will trim trailing whitespaces, fix extra newlines
  at the end of the file and run `flake8` and `black` for linting and
  autoformatting.
- [`pytest`](https://docs.pytest.org): Run unit tests using `pytest tests`
- [`sphinx`](https://www.sphinx-doc.org/): Used to generate documentation from the `docs` folder. There is a
  Makefile in the docs folder which can generate documentation in various
  formats, such as HTML (`make html`).

Development on major features follows the [Github
flow](https://guides.github.com/introduction/flow/) model. There is a [project
changelog](CHANGELOG.md) following the [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/) guide to keep track of major
changes for each release.

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

- **Scraping**. **requests** for fetching data over HTTP, **beautifulsoup4** for
  HTML parsing. **nltk** is used to clean the text data. All of these are well-known, widely used libraries.

  Licenses: Apache (requests, nltk), MIT (beautifulsoup4)

- **Database**. Connection to MongoDB is done via [**pymongo**](https://pymongo.readthedocs.io/) (Apache license).

- **CLI**. [**fire**](https://github.com/google/python-fire) is used to easily
  create the command line interface and
  [**tqdm**](https://tqdm.github.io) is used to display progress bars during
  training and prediction. Both of these libraries are well-maintained but can
  be removed if required, with fire being replaced by argparse and removing
  progress bars.

  Licenses: Apache (fire), MIT (tqdm)
