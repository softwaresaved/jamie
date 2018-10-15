# jobs-analysis

This project aims to monitor and analyse the number of academic jobs, mainly in the UK, that require software skills. It does this by scraping jobs posted on the [job.ac.uk](https://www.jobs.ac.uk/) (academic jobs) website every day and stores these as file fragments.  These files are then pushed into a database. A classifier is then run to determine whether each job is a `Software Research Job` or not.  By a `Software Research Job` we mean a job that requires some level of software development. A job that uses software as an end-user is not a Software Research job.

## Description of the project

The aim of this work is to understand what are the characteristics of the `Software Research Job` job in academia  and how it evolves over time.
One way to find out, aside of asking RSE directly, it is to study the job ads directly. They contain information about `salary`, `type of contract`, `location`, or duration for instance.
For that purpose we downloaded the ads that are published on the website [jobs.ac.uk](www.jobs.ac.uk) and classify these ads between *Research Software Development* jobs and *Not Research Software Development*. These classifications are later used to have an insight on different metrics for the Research Software jobs specifically.

In practice, it is possible to decompose the project into 3 distinct steps: **data collection and cleansing**, **prediction** and **analysis**. Each of these steps are conducted everyday automatically with a [bash script](day_task.sh).

### [Data collection and cleansing](https://github.com/softwaresaved/jobs-analysis/tree/master/jobAnalysis/dataCollection)

Collecting the jobs ads in a naive way and store then into a file for further analysis.

#### Data collection

It is an html scraper built with python and [beautifulSoup](https://pypi.org/project/beautifulsoup4/) to parse the html content. It uses the search feature on the website to collect the links of all jobs posted on the website. With that information, it recreates the URL to download the html content of all each job ads into a separated file. Each file is supposed to have an unique ID parsed from that website. It ensures we do not store twice the same jobs.
That file is preprocessed only to store the valuable sections (remove the header and footer) and there is no other transformation at this step.

The job collection spams from 2013 until today. Any details about the dataset, the raw data, the data missing, etc, can be found in the [dataCollection notebook](./notebooks/dataCollection.ipynb).

#### Data cleansing

After downloading and storing the jobs into the file, a cleaning operation is done over these files.

Sometimes the ads does not contains the information we want or the formatting of the field is not following the rules we expect. This data cleaning focus on different keys as described below. Once the job ads is cleaned it is stored into a MongoDB to facilitate further steps.

* **Description**: This key contains the description of the job. It is essential to classify the job. In case of absence, the job ads is discarded.

* **Date of publishing**: The date of publishing, stored under the key `placed_on`, is essential to be able to do an analysis over time.

* **Salary**: This information is essential for our analysis. it is a text field that we convert into two piece of information. One is the lower salary and the second is the higher salary upon negotiations/skills/... The maximum effort is made to extract this two information, but if it is impossible, the job ads is discarded. This could be the case when that field does not contain information about salary (usually under the line of 'Competitive' or 'Not specified') or contains salary in hours or in foreign currencies.

* **Employer**: This is which employer posted the job ads. We are only interested in Universities in United-Kingdom. Therefore we use a list of all universities in UK (that can be found [here]()) and only keep the ones that matches an element in that list.

* **Type of role**: This field is an array of the type of job is given. It can be one or more of these values: [`Academic or Research`, `Professional or Managerial`, `Technical`, `Clerical`, `Craft or Manual`, `PhD`, `Masters`]. This is used to filter out all the ads about a `PhD` position or a `Master`, as it is not our interest. All others job ads are kept for further analysis.

At the end of this cleaning process, the results are stored into a MongoDB with all the cleaned information. This is the dataset used for any analysis and report.

### [Predicting the type of job](https//github.com/softwaresaved/jobs-analysis/tree/master/jobAnalysis/dataPrediction)

Each new added jobs into the database get a prediction to know if they are a Software development position or not.
To build the predictive model, two one-shot operations were needed. We needed to collect a training set and building the model itself.

#### Creating a training set

To classify the jobs in two categories we needed to have a training dataset. We asked expert to read a subset of Job Ads as presented on the website (without pictures) in which category that jobs fallen into. They had the choice between 4 options:
* This job ads is mostly for a Software development position.
* This jobs requires some software development.
* This jobs does not requires software development.
* There is not enough information to decide.

Each jobs ads were shown several times (up to three times) to different experts until a consensus emerged.
A job is classified as *Software job* if two participants assigned *Most* or *Some* to the question: **How much of this person's time would be spent developing software?**. If no consensus emerged, the job was classified *Ambigous* and if there was not enough information the job was classified *Insufficient Evidence*.
Only the Software Jobs and Not software jobs are kept for building the model.

The dataset is composed of **1262** classified jobs. There are **335** jobs classified as Software Jobs and **813** as not *Software job*.

|Type of classification | Count | Percentage|
| :-: | :-: | :-: |
No Software Job | 813 | 64%
Software Job | 335 | 27%
Ambiguous | 69 | 5%
Insufficient Evidence | 45 | 4

#### Building a model

To build a model, the package [scikit-learn](http://scikit-learn.org/stable/) was used. The model creation implies a feature selection and then a model selection. The model (and diverse metrics and results) is then stored into a [file]('./outputs/dataPrediction/model.pkl') as well as the [feature pipeline]('./outputs/dataPrediction/features.pkl') and use to classify any new jobs.

##### Feature selection

The main key used for feature selection is the `description` key that contains the information about the jobs
The second key used is `job title`  which is a text field that represents the title of the job ads and often contains the title of the job.
The third key used is the number of time a word from a pre-made list appears in the description text. This list contains words that we think are associate with software. The list can be found [here]('./jobAnalysis/common/search_term_list.py').

The text fields (`description` and `job title`) had their stop words removed, and were transformed using TF-IDF for both 1-gram and 2-grams.
The count of words from the software list was transformed into a category. Each of the number associated representedcategories.

A feature pipeline was build and fed to the model selection step.

##### Model selection

We selected the best model with nested-cross validation. At the end, the model chosen was the `Gradient Boosting` as it was the most stable and the most precise model. To select the model, the `precision` metric was use rather than the `accuracy` ones due to the unbalanced dataset (more None Research Software Job).

Once the model was selected, we run it to an unseen dataset. This testing dataset was created at the beginning of the process by splitting the total dataset into two (using stratified sampling). The first subset (80% of the dataset) was used for the model selection and training. The second subset (20%) was used to check the model.

Once we tested the model on the unseen dataset, we re-train the selected model on the total dataset.


The confusion matrix applied to the unseen dataset (20% of the total training set) shows that the model predicts accurately **75%** of the Research Software Job correctly (True Positives) and in 25% of the case seen it labels incorrectly a Research Software job as Non Software Job (false negative). It also shows that the model mislabels `non Software Job` as `Software job` in **2%** of the cases (false positives) which is really low but it is due to the unbalanced dataset (more Non Software Jobs).

To conclude that confusion matrix. It is possible to understand it as: ***our model predict accuratly a Research Software job in 75% of the cases it seen.***


Here the plot of the confusion matrix. For further details on the process of model creation and selection, please refer to the [Data Prediction notebook](./notebooks/dataPrediction.ipynb).

![Confusion matrix with normalisation](./outputs/png/confusion_matrix_normalised.png?raw=true "Title")


### [Analysis of the dataset](https://github.com/softwaresaved/jobs-analysis/tree/master/jobAnalysis/dataAnalysis)

This is a collection of scripts that parse the database to output different csv files containing all the information needed ([here](https://github.com/softwaresaved/jobs-analysis/tree/master/outputs)) for the [jupyter notebooks](https://github.com/softwaresaved/jobs-analysis/tree/master/notebooks) to display the statistiques and information about the project.

After subsetting the raw dataset for jobs ads that are **not** a `PhD` or a `Master` position, have a `salary field` cleaned and are from an `university` located in `United-Kingdom`, as well as a cleaned `date of publication` and it is classified either as a Software Jobs and Not Software jobs.

These classifications are made after using the [training-set-collector](https://github.com/softwaresaved/training-set-collector) to obtain a training set for building a model using the [modelCreation](https://github.com/softwaresaved/jobs-analysis/tree/master/jobAnalysis/modelCreation) scripts.


## Automated process

All these described steps are run every days using the [day_task.sh](day_task.sh) script. This script do the following steps in order
1. Checkout into `reports branch`.
1. Overwrite that branch with the `master branch` with a `pull --merge --theirs`.
1. Run the [getJobs.py script](./jobAnalysis/dataCollection/getJobs.py) to collect new jobs from the [dataCollection folder](./jobAnalysis/dataCollection) .
1. Run the [job2db.py script](./jobAnalysis/dataCollection/job2db.py) to clean the new jobs and store them into the MongoDB.
1. Run the [run.py script](./jobAnalysis/dataPrediction/run.py) to predict the type of jobs it is and store the value into the document into the DB.
1. Run the [collect_info.py script](./jobAnalysis/dataAnalysis/collect_info.py) to collect csv files from [dataAnalysis folder](./jobAnalysis/dataAnalysis) and store them into the [outputs folder]('./outputs/).
1. Run all separated notebooks to update the results with the newly added jobs from the [notebooks folder](./notebooks/).
1. Push the new updated documents to the `reports` branch by overwriting it.


## Deployment

For a detailed description to deploy this project, please read the [deployment plan](./Depolyment.md).

## Branches

This is the list of different branches present in the repository.
* **Active branches**: Only these branches are currently used:
    * `master`: The master branch
    * `dev_olivier`: Olivier's development branch.
    * `reports`: Branch were reports are automatically uploaded. It pull the master branch, overwrite it and then push the new reports -- Do not modify that branch, it is for read only
    * `legacy`: Right after the release [legacy](https://github.com/softwaresaved/jobs-analysis/releases/tag/legacy) the master branch has been copied in this branch. All the previous code is in there [Only for archive reason].

* **Legacy branches**: These branches remain in the repo but they are not used anymore:
    * `dissertation`: MSc project work being undertaken by Shicheng Zhang.
    * `iaindev`: Iain's development branch.
    * `mariodev`: Mario's development branch.
    * `ssi`: Iain's human classifier to build a training set based on the work done by Ernest.
    * `stevedev`: Steve's development branch.
