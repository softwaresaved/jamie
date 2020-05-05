# jobs-analysis

This project aims to monitor and analyse the number of academic jobs, mainly in the UK, that require software skills. It does this by scraping jobs posted on the [job.ac.uk](https://www.jobs.ac.uk/) (academic jobs) website every week day and stores these as file fragments.  These files are then pushed into a database. A classifier is then run to determine whether each job is a `Software Research Job` or not.  By a `Software Research Job` we mean a job that requires some level of software development. A job that uses software as an end-user is not a Software Research job.

**Note**: This branch (`jamie`) is a work in progress, so this README is constantly in flux.

## Description of the project

The aim of this work is to understand what are the characteristics of the `Software Research Job` job in academia  and how it evolves over time.
One way to find out, aside of asking RSE directly, it is to study the job ads directly. They contain information about `salary`, `type of contract`, `location`, or duration for instance.
For that purpose we downloaded the ads that are published on the website [jobs.ac.uk](www.jobs.ac.uk) and classify these ads between *Research Software Development* jobs and *Not Research Software Development*. These classifications are later used to have an insight on different metrics for the Research Software jobs specifically.

In practice, it is possible to decompose the project into 3 distinct steps: **data collection and cleansing**, **prediction** and **analysis**. Each of these steps are conducted everyday automatically with a [bash script](day_task.sh).

### [Data collection and cleaning](https://github.com/softwaresaved/jobs-analysis/tree/master/jobAnalysis/dataCollection)

Collecting the jobs ads in a naive way and store then into a file for further analysis.

#### Data collection -- `jamie scrape`

This uses an html scraper built using Python and [beautifulSoup](https://pypi.org/project/beautifulsoup4/) to parse the html content. It uses the search feature on the website to collect the links of all jobs posted on the website. With that information, it recreates the URL to download the html content of each job ads into a separate file. Each file is supposed to have an unique ID parsed from that website. It ensures that we do not store the same jobs twice.
That file is preprocessed only to store the valuable sections (removes the header and footer) and there is no other transformation at this stage.

The job collection spams from 2013 until today. Any details about the dataset, the raw data, the missing data, etc, can be found in the [dataCollection notebook](./notebooks/dataCollection.ipynb).

#### Data import -- `jamie import`

After downloading and storing the jobs into the file, a cleaning operation is done over the files.

Sometimes the ads do not contain the information we require or the formatting of the field does not follow the rules we expect. This data cleaning focus on the different keys described below. Once a job ads is cleaned it is stored in MongoDB to facilitate subsequent steps.

* **Description**: This key contains the description of the job. This is essential to classify the job. In case of absence, the job ads is discarded.

* **Date of publishing**: The date of publishing, stored using the key `placed_on`, is essential to do an analysis over time.

* **Salary**: This information is essential for our analysis. it is a text field that we convert into two piece of information. One is the lower salary and the second is the higher salary upon negotiations/skills/... The maximum effort is made to extract this two information, but if it is impossible, the job ads is discarded. This could be the case when that field does not contain information about salary (usually using the line of 'Competitive' or 'Not specified') or contains salary in hours or in foreign currencies.

* **Employer**: This is the employer posted the job ads. We are only interested in Universities in United-Kingdom. Therefore we use a list of all universities in UK (that can be found [here](jobAnalysis/dataCollection/data/uk_uni_list.txt)) and only keep the ones that matches an element in that list.

* **Type of role**: This field is an array of the type of job is given. It can be one or more of these values: [`Academic or Research`, `Professional or Managerial`, `Technical`, `Clerical`, `Craft or Manual`, `PhD`, `Masters`]. This is used to filter out all the ads about a `PhD` position or a `Master`, as it is not our interest. All others job ads are kept for further analysis.

At the end of this cleaning process, the results are stored into a MongoDB with all the cleaned information. This is the dataset used for any analysis and report.

### [Predicting the type of job](https//github.com/softwaresaved/jobs-analysis/tree/master/jobAnalysis/dataPrediction)

Each new added jobs into the database get a prediction to know if they are a Software development position or not.
To build the predictive model, two one-shot operations were needed. We needed to collect a training set and to build the model itself.

#### Creating a training set

To classify the jobs in two categories we needed to have a training dataset. We asked experts to read a subset of Job Ads as presented on a website (without pictures) in which category that jobs fallen into. They had the choice between 4 options:
* This job ads is mostly for a Software development position.
* This jobs requires some software development.
* This jobs does not requires software development.
* There is not enough information to decide.

Each jobs ads were shown several times (up to three times) to different experts until a consensus emerged. The aggregation procedure is shown in detail here TODO.

#### Building a model -- `jamie train`

To build a model, the package [scikit-learn](http://scikit-learn.org/stable/) was used. The model creation implies a feature selection and then a model selection. The model (and diverse metrics and results) is then stored into a [file]('./outputs/dataPrediction/model.pkl') as well as the [feature pipeline]('./outputs/dataPrediction/features.pkl') and use to classify any new jobs.

##### Feature selection

The main key used for feature selection is the `description` key that contains the information about the jobs
The second key used is `job title`  which is a text field that represents the title of the job ads and often contains the title of the job.
The third key used is the number of time a word from a pre-made list appears in the description text. This list contains words that we think are associate with software. The list can be found [here]('./jobAnalysis/common/search_term_list.py').

The text fields (`description` and `job title`) had their stop words removed, and were transformed using TF-IDF for both 1-gram and 2-grams.
The count of words from the software list was transformed into a category. Each of the number associated representedcategories.

A feature pipeline was build and fed to the model selection step.

##### Model selection and prediction

Model selection comprises a few steps. For each step the corresponding command is shown in brackets:

- **Training data snapshot** (`snapshot-training-data`): Before we run any models, we take a snapshot of the database subset used for training. The subset is chosen from the file `tags_summary.json`. We snapshot the data for reproducibility purposes. Snapshot data is stored in `snapshots/training/DATE`. Snapshots can be listed by running `jamie list-snapshots training`
- **Model Selection** (`model-selection`): We run a series of models (to add a model, add a module under `jamie.models` using nested cross validation. The model outputs are stored in `snapshots/models/<codedate>_train<training-snapshot-date>_<code_githash>/<modelname>.pkl` for the pickled models and `<modelname>_features.npz` for the features. The current model configuration is also saved as `model.toml` in the folder. The best model files are symlinked as `best_model.pkl` and `best_model_params.json`. In case the links are lost, we also write a summary of the whole run in a `summary.json` file. By default, `model-selection` uses the latest training snapshot, but a specific snapshot can be specified by adding the training snapshot name:

    jamie model-selection training-snapshot  # use 'list-snapshots training' to see options

The list of model snapshots can be obtained by `jamie list-snapshots models`.

- **Prediction** (`predict`). The model training automatically produces scores (in our case using the precision metric) for the models under `jamie.models`. The best model is also picked in the model selection phase. For prediction, we run the chosen model against the live database and record the predictions in a separate collection called `predictions`, which is indexed by `jobid`. By default, the best model from the latest model snapshot (by code and training date) is selected for prediction. The predictions are tagged with the model snapshot. Specific snapshots can also be specified as follows:

    jamie predict <model-snapshot>  # use 'list-snapshots models' to see options.
    jamie predict <model-snapshot> <model-name>  # for a particular model

To obtain confidence intervals, we run an ensemble of `model.ensemble_size` (default: 100) models with different train-test splits. For ensemble runs, we store the predictions for each of the models along with a summary in `snapshots/predictions/<model-snapshot>`. Note that we assume the prediction code has not changed between training the model and the time when the prediction was run. We also do not expect reproducibility here, as the live database is changing all the time.

### Reports (`report`)

Reporting is done using a web frontend written in Flask, running simple plots and summarising the information. The report is segmented into sections, each of which is a separate module under `jamie.report`. The frontend can be launched by typing

    jamie report [--port=PORT]  # by default, launches on port 8080

## Automated process

TODO

## Branches

This is the list of different branches present in the repository.
* **Active branches**: Only these branches are currently used:
    * `master`: The master branch
    * `jamie`: The development branch for the next version
* **Legacy branches**: These branches remain in the repo but they are not used anymore:
    * `reports`: Branch were reports are automatically uploaded. It pull the master branch, overwrite it and then push the new reports -- Do not modify that branch, it is for read only
    * `legacy`: Right after the release [legacy](https://github.com/softwaresaved/jobs-analysis/releases/tag/legacy) the master branch has been copied in this branch. All the previous code is in there [Only for archive reason].
    * `dev_olivier`: Olivier's development branch.
    * `dissertation`: MSc project work being undertaken by Shicheng Zhang.
    * `iaindev`: Iain's development branch.
    * `mariodev`: Mario's development branch.
    * `ssi`: Iain's human classifier to build a training set based on the work done by Ernest.
    * `stevedev`: Steve's development branch.
