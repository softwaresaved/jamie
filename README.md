***DO NOT FORK THIS REPOSITORY!***
# jobs-analysis
This analyses jobs data to identify trends in job types related to software development. This is the master branch. Other branches in this repository consist of:

* `dissertation` - MSc project work being undertaken by Shicheng Zhang.
* `iaindev` - Iain's development branch.
* `mariodev` - mario's development branch.
* `ssi` - Iain's human classifier to build a training set based on the work done by Ernest.
* `stevedev` - Steve's development branch.

## Files

* `classifier-app` - an app that faciliates tthe classifying of software jobs - could be used to build a training set.
* `data` - some data required for the job analysis.
* `job2db` - Python scripts to parse html job fragments -- clean the information -- Record the result into a MongoDB database
* `jobs-data-etl` - scripts implementing an extract, transform and load (ETL) process for jobs data.
* `jobstats` - using python to analyse the data.
* `scripts` - Perl script used to scrape job information, Perl script to process the job files and flatten these into a csv file. R scripts that do analysis of the jobs.csv file. Some of the results can be found in the [project wiki](https://github.com/softwaresaved/jobs-analysis/wiki).

