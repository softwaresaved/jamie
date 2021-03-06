![jamie](docs/jamie-small.png)

![Python 3.8](https://github.com/softwaresaved/jamie/workflows/Python%203.8/badge.svg?branch=master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Jobs Analysis using Machine Information Extraction** (JAMIE) is a tool that
aims to monitor and analyse the number of academic jobs, mainly in the UK, that
require software skills.

**[Documentation](http://jamie.trenozoic.net)** •
**[Contribution Guidelines](CONTRIBUTING.md)** •
**[Machine Learning](ML.md)**

There is a [**research software jobs tracker**](http://rsejobs.trenozoic.net)
which is an instance of jamie that tracks software jobs in
UK universities.

## Prerequisites

1. **OS**. Any UNIX based OS can be used to run jamie. Development was done on
   Debian 11 (testing, bullseye), Ubuntu 20.04 should work as well.
1. **Python**. Development uses Python 3.8, though later versions should work
   as well.
1. **Database**. Jamie uses MongoDB as the backing store for jobs data. Either
   [install MongoDB locally](https://docs.mongodb.com/manual/installation/) or
   connect to a MongoDB database by setting a [valid MongoDB connection
   URI](https://docs.mongodb.com/manual/reference/connection-string/) (with
   username and password, if required) in the `JAMIE_MONGO_URI` environment
   variable.

   The database uses the name `jobsDB`. If such a database already exists in the MongoDB, then either rename it or set the database name using `jamie config db.name <newname>`.

1. **Setup**. Run `jamie setup`. This (i) checks the database connection, (ii)
   downloads necessary NLTK datasets which are needed for text cleaning, and
   (iii) checks that a training set exists.

## Installation

To install using pip:

    git clone https://github.com/softwaresaved/jamie.git
    cd jamie
    python3 -m venv .venv
    source .venv/bin/activate
    pip install .
    pip install .[dev,docs]  # For development work

## How it works

The CLI tool `jamie` is a wrapper around the Jamie API (see the documentation).
Working with Jamie is similar to running standard machine learning pipeline: we
first train a model and use that to predict whether jobs are software jobs or
not. The final step is the creation of the report.

![workflow](docs/workflow.svg)

You can take a look at the **[detailed
workflow](http://jamie.trenozoic.net/workflow.html)** along with the
help for the command line interface, or look at how we **[built the
model](http://jamie.trenozoic.net/methods.html)**.

**Concurrency**. All the steps indicated above with `snapshots` support
multiple snapshots, and independent snapshots can be worked on concurrently.
Scraping writes to the filesystem and can be run independently of other steps
as well. Prediction requires read access to the database, so running it
concurrently with the load step (which writes to the database) might not work
or result in unpredictable behaviour. This can be fixed by making prediction
work from a database snapshot (not currently supported).

**Reproducibility**. Training the model should be reproducible and the random number seed is set automatically where needed. Scraping is inherently non-reproducible, but loading and cleaning the data should be (not tested yet). Prediction is non-reproducible as it relies on a mutable database, but generation of reports from predictions is reproducible.

## Usage

Detailed usage can be found in the
[workflow](http://jamie.trenozoic.net/workflow.html) document.

1. **Configuration**: Show the configuration using `jamie config`, or set
   configuration using `jamie config <configname> <value>`
1. **Download** jobs: `jamie scrape`
1. **Load** jobs into MongoDB: `jamie load`. Pass option `--dry-run` to test.
1. **Training snapshots**: A training snapshot is needed to run the machine
   learning pipeline. First check the snapshots folder location (`jamie config
   common.snapshots`), exists and then copy an existing training set CSV file
   into the training snapshot location. It should be called `training_set.csv`:

       cd `jamie config common.snapshots`
       mkdir -p training/<date>  # date of snapshot
       cp /path/to/training_set.csv training/<date>

1. **Train** the model: `jamie train [<snapshot>]`. If snapshot is not
   specified, uses the latest snapshot.
1. **Predict classification**: The previous command will create model snapshots
   in `<snapshots>/models` of the snapshots location. You can now use these
   snapshots to make predictions: `jamie predict [<snapshot>]`. This saves the
   prediction snapshot in `<snapshots>/predictions`.
1. **Generate report** corresponding to the prediction snapshot: `jamie
   report`. The report is created in `<snapshots>/reports` with the same name
   as the corresponding prediction snapshot. To view the report, run

       # If snapshot not specified, see latest report
       jamie view-report [<snapshot>]

   This will start a local webserver for viewing the report. The report
   snapshot folder is self contained and can be served using standard
   webservers as well.
