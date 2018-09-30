# jobs-analysis

This project aims to monitor and analyse the number of academic
jobs, mainly in the UK, that require software skills. It does this
by scraping jobs posted on the [job.ac.uk](https://www.jobs.ac.uk/)
(academic jobs) website every day and stores these as file fragments.
These files are then pushed into a database. A classifier is then run
to determine whether each job is a Software Research Job or not.
By a Software Research Job we mean a job that requires some level of
software development. A job that uses software as an end-user is not
a Software Research job.

## Description of the project

The aim of this work is to understand what are the characteristics of the Research Software Developer job in academia  and how it evolves over time.
One way to find out, aside of asking RSE directly, it is to study the job ads directly. They contain information about salary, type of contract or duration for instance.
For that purpose we downloaded the ads that are published on the website [jobs.ac.uk](www.jobs.ac.uk) and classify these ads between *Research Software Development* jobs and *Not Research Software Development*. These classifications are later used to have an insight on different metrics for the Research Software Development specifically.

In practice, it is possible to decompose the project into 4 distinct steps: **data collection and cleansing**, **prediction** and **analysis**. Each of these steps are conducted everyday automatically with a [bash script](day_task.sh). Here  a brief description of each of these steps, what are their purpose and which technology they use


### [Data collection and cleansing](https://github.com/softwaresaved/jobs-analysis/tree/master/jobAnalysis/dataCollection)

Collecting the jobs ads in a naive way and store then into a file for further analysis.

#### Data collection

It is an html scraper build with python and [beautifulSoup]() to parse the html content. It uses the search feature on the website to collect the link of all jobs posted on the website. With that information, it recreates the URL to download the html content of all the new job ads into a separated file. Each file is supposed to have an unique ID parsed from that website. It ensures we do not store twice the same jobs. That file is preprocessed only to store the valuable sections (remove the header and footer).


#### Data cleansing

Cleaning the dataset to see which of them are usable. Sometimes the ads does not contains the information we want or the formatting of the field is not following the rules we expect. This data cleaning focus on different keys as describe below. Once the job ads is cleaned it is stored into a MongoDB to facilitate further steps.

* **Description**: This key contains the description of the job. It is essential to classify the job. In case of absence, the job ads is discarded.

* **Date of publishing**: The date of publishing, stored under the key `placed_on`, is essential to be able to do an analysis over time.

* **Salary**: This information is essential for our analysis. it is a text field that we convert into two piece of information. UOne is the lower salary and the second is the higher salary upon negotiation/skills/... The maximum effort is made to extract this two information, but if it is impossible, the job ads is discarded. This could be the case when that field does not contain information about salary (usually under the line of 'Competitive' or 'Not specified') or contains salary in hours or in foreign currencies.

* **Employer**: This is which employer posted the job ads. We are only interested in Universities in United-Kingdom. Therefore we use a list of all universities in UK (that can be found [here]()) and only keep the ones that matches an element in that list.

* **Type of role**: This field is an array of the type of job is given. It can be one or more of these values: [`Academic or Research`, `Professional or Managerial`, `Technical`, `Clerical`, `Craft or Manual`, `PhD`, `Masters`]. This is used to filter out all the ads about a `PhD` position or a `Master`, as it is not our interest. All others job ads are kept for further analysis


### [Predicting the type of job](https//github.com/softwaresaved/jobs-analysis/tree/master/jobAnalysis/dataPrediction)

This step applies a predictive model that predicts if the job ads is about a Software Development position or not. This step is done for each new job ads added to the database. However to build the predictive model, two `one-shot` operations were needed. We needed to collect a training set and building the model itself.

* **Training set**: To classify the jobs in two categories we needed to have a training dataset. We asked expert to read a subset of Job Ads to tell us if the jobs seems to contain Software Development aspect, if it does not contain any, if it was ambiguous (not sure) or if the ads did not contain enough information. Each jobs ads were shown several times to different experts until a consensus emerged (see [] about the rules).

* **Training the model**: To build a model, the package sklearn was used. This modeling steps contains 2 steps itself. The feature selection and the model training.


### [Analysis of the dataset](https://github.com/softwaresaved/jobs-analysis/tree/master/jobAnalysis/dataAnalysis)

This is a collection of scripts that parse the database to output different csv files containing all the information needed ([here](https://github.com/softwaresaved/jobs-analysis/tree/master/outputs)) for the [jupyter notebooks](https://github.com/softwaresaved/jobs-analysis/tree/master/notebooks) to display the statistiques and information about the project.

After subsetting the raw dataset for jobs ads that are not a PhD or a master position, have a salary field cleaned and are from an university located in United-Kingdom, as well as a cleaned date of publication and it is classified either as a Software Jobs and Not Software jobs.


These classifications are made after using the
[training-set-collector](https://github.com/softwaresaved/training-set-collector)
to obtain a training set for building a model using the
[modelCreation](https://github.com/softwaresaved/jobs-analysis/tree/master/jobAnalysis/modelCreation)
scripts.


## Automated process

All these described steps are run every days using the [day_task.sh](day_task.sh) script.



## Deployment

For a detailed description to deploy this project, please read the [deployment plan](./Depolyment.md).

## Branches
This is the list of different branches present in the repository.
* **Active branches**: Only these branches are currently used:
    * `master`: The master branch
    * `dev_olivier`: Olivier's development branch.
    * `reports`: Branch were reports are automatically uploaded. It pull the master branch, overwrite it and then push the new reports -- Do not modify that branch, it is for read only
    * `legacy`: Rigth after the release [legacy](https://github.com/softwaresaved/jobs-analysis/releases/tag/legacy) the master branch has been copied in this branch. All the previous code is in there [Only for archive reason].

* **Legacy branches**: These branches remain in the repo but they are not used anymore:
    * `dissertation`: MSc project work being undertaken by Shicheng Zhang.
    * `iaindev`: Iain's development branch.
    * `mariodev`: mario's development branch.
    * `ssi`: Iain's human classifier to build a training set based on the work done by Ernest.
    * `stevedev`: Steve's development branch.
