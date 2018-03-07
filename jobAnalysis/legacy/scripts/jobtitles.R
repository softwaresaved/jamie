#!/usr/bin/env Rscript
#
# R script to create a summary of the jobs data. The script reads
# in the data from the jobs.csv file and processes this writing the
# output to an summary/index.html file.
#

# Load libraries that are required
library(lattice)
library(R2HTML)

# Popular job titles
#
# Returns a sorted table of job titles and number of times they occur
# Currently doesn't try and cluster based on partial matches
# i.e. Research Assistant and Research Assistant in Foo are separate

jobtitlefrequency <- function(jobs) {

  return(sort(table(jobs$Name, useNA = "ifany")))

}

#######################
# Reading in the data #
#######################

  # Column names for the CSV data.
  cn = c("JobId",
        "Name",
        "Employer",
        "Location",
        "InUK",
        "SoftwareJob",
        "SoftTermIn",
        "Salary",
        "SalaryMin",
        "SalaryMax",
        "Hours",
        "Contract",
        "Placed on",
        "Closes",
        "Job Ref",
        "h1",
        "h2",
        "h3",
        "Role",
        "Subject",
        "Location2",        
        "Description")


  # Define the Russell group of Universities
  russell <- c("university-of-birmingham",
               "university-of-bristol",
               "university-of-cambridge",
               "cardiff-university",
               "durham-university",
               "university-of-edinburgh",
               "university-of-exeter",
               "university-of-glasgow",
               "imperial-college-london",
               "kings-college-london",
               "university-of-leeds",
               "university-of-liverpool",
               "london-school-of-economics-and-political-science",
               "the-university-of-manchester",
               "newcastle-university",
               "university-of-nottingham",
               "university-of-oxford",
               "queen-mary-university-of-london",
               "queens-university-belfast",
               "university-of-sheffield",
               "university-of-southampton",
               "university-college-london",
               "university-of-warwick",
               "university-of-york"
  )

# Read the data into data (a data frame)
alljobs<-read.csv(file="../data/jobs.csv",encoding="UTF-8",col.names=cn)

# Create subset of just software related jobs
swjobs <- subset(alljobs, SoftwareJob == "1")

alljobtitles <- jobtitlefrequency(alljobs)
swjobtitles <- jobtitlefrequency(swjobs)

##############################
# Writing out a summary file #
##############################

HTMLStart(outdir="summary", file="jobtitles",
  	extension="html", echo=FALSE, HTMLframe=FALSE)
HTML.title("Job Titles Analysis", HR=1)

HTML.title("Description of my data", HR=3)

HTML(paste("Total number of jobs analysed:"), CSSFile="")
HTML(length(alljobs$JobId))

HTMLhr()

HTML.title("Most popular job titles - all jobs", HR=3)
tail(alljobtitles, 10)

HTMLhr()

HTML.title("Most popular job titles - software jobs", HR=3)
tail(swjobtitles, 10)


HTMLStop()
