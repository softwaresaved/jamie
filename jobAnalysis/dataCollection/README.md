# Jobs to CSV

author: Olivier Philippe

## Description

This directory is used to build the parser that inputs HTML excerpt files containing the job data, cleans them and inserts them into a MongoDB instance.

All the operation are done by the `job2db.py` script.


### Parsing

The script parses the folder containing the html file and create a list of `JobId`s (the names used for the files). Then it compare this list with the already recorded list into the database by querying the same key.
The difference is then send to `fileProcess.py` for the transformation of the file.

It compares the name of the file with two list: `SKIPPED_ID` and `RECORDED_ID`. If the name of the file is present in one of these lists it is skipped.
The file is opened and the he content is passed to the `fileProcess.py` and transformed with bs4.
A first cleaning transformation is done on the key and return a dictionary.


### Cleaning

Cleaning of the parsed jobs data file according to the "Data cleaning operation" diagram at https://goo.gl/qTsptq.


### Loading


Cleaning of the parsed jobs data CSV file according to the "Data cleaning operation" [diagram](https://goo.gl/qTsptq).

When the file is parsed, the result is recorded in RECORDED_JOB and the name is added in RECORDED_ID. If the parsing failed the name is added in the SKIPPED_ID name.


## Requirements

* Use Python 3.5
* pip install -r requirements.txt

## Files

* `job2db.py` - the wrapper to do the parsing - cleaning - loading.
* `requirements.txt` - a TXT file that contains a list of  libraries needed to launch `jobs2csv.py`
* `config.ini` - an INI files containing the variables that are needed to be set up
    * `INPUT_FOLDER` - Folder containing the htm files
    * `DB_ACCESS_FILE` - Filename containing the information to connect to the mongoDB -- Stored into svm but not github
* `logs/` - Folder where the logs created by the `job2db.py` are recorded
* `include/` - Various needed PYTHON scripts for `jobs2csv.py`
    * `configParser.py` - Modification of the configparser to parse list as argument
    * `fileProcess.py` - Transformation of the htm file into a python dictionary. Some rudimentary cleaning rules but no information loss
    * `cleaningInformation.py` - the cleaning process decided in [diagram](https://goo.gl/qTsptq).

* `job4bob.py` - a Python script to copy a list of files to another folder used by the web classifier Bob. The rules are defined in the document `job4bob.md`

* `job4bob_config.ini` - config file for `job4bob.py`


### Installation

* Install the dependencies with `pip install -r requirements.tx`'
* Configure the option in config.ini for the INPUT_FOLDER and DB_ACCESS_FILE in the `config.ini`
* Simply run `python3.5 job2db`.


## Selection of sample

The script [job4bob.py](./job4bob.py) is used to output a list of jobsId that met the criteria for Bob.
The sample given to the RSE people to classify

The set of jobs used to do the classification comprise of 88501 jobs frozen on the 15/11/2017.
This set excludes all jobs that jobs.ac.uk labelled as `Master`, `PhD` and `Clerical`.
It also excludes the jobs that have been labelled as owning an `InvalidCode` as defined in [diagram](https://goo.gl/qTsptq) and implemented in [/include/cleaningInformation.py](./include/cleaningInformation.py).

The summary of the database at the time of the frozen state is as followed.


| Type Role                  |   Clean Result | Invalid Code |   **Total** |
|:---------------------------|:--------------:|:------------:|------------:|
| Academic or Research       |          56930 |        19545 |   **76475** |
| Clerical                   |          15219 |         3779 |   **18998** |
| Craft or Manual            |           2590 |          947 |    **3537** |
| Masters                    |             47 |          322 |     **369** |
| PhD                        |            276 |        11581 |   **11857** |
| Professional or Managerial |          26011 |         8211 |   **34222** |
| Technical                  |           6627 |         1506 |    **8133** |
| **Total**                  |   **107700**   |  **45891**   |  **153591** |


The sample contains jobs that are labelled `Academic or Research` (56930), `Craft or Manual` (15219), `Professional or Managerial` (26011), and `Technical` (6627).

