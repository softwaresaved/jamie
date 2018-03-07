# Scripts directory

Some of the scripts that are used to generate and analyze the data.

## Data generation

The following two scripts have been placed here for completeness. They should not be run.

* `getJobs.pl` - Perl script used to scrape jobs from jobs.ac.uk. This file is run every week day at 5am and it scrapes any new jobs. The job files are kept as html excerpts (not proper html) on the ssi-data.epcc.ed.ac.uk server. The collective data files are too big to be put on this server.
* `job2csv.pl` - Perl scipt that converts job files into a csv format file. This takes the html excerpts produced by the `getJobs.pl` scripts and flattens into a commas separated values file. This file is too big to put in the repository as well.

## Data processing

* `jobtitles.R` - R script to analyze the job titles.
* `languages.sh` - shell script to grep through the data. Not really meant to be a serious processing 
  script but to allow some basic investigation of the data, expanding the computing language basis
  and noting down what some of the issues are.
* `process.R` - R script to do some basic analysis to generate some summary data. This assumes that
   the `jobs.csv` file is in the `../data` directory.
* `R/filestuff.R` - routines to read the `jobs.csv` file and put it in an R data frame. Also has another routine to clean 
  the locations information.
* `Rutilities.R` - playing with different bits of R functionality. Once anything here becomes sufficiently 
   mature it will be migrated to other separate scripts.
* `TextMining.R` - trying to use the R `tm` package. Do not run this as a script.
* `maps.R` - attempt to generate geographical renderings of the data.
* `R` - directory containing common functions for the above scripts.


## Other relevant documents

* [Questions](Questions.md) - archives a set of questions to be answered.
* [R resources](Rresources.md) - a list of useful R-related links.

