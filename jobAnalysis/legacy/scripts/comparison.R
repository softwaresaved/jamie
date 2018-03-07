
# Need this for the Cross comparison
library(gmodels)

# Need this for the not in operator (%nin%)
library(Hmisc)

# Set the working directory
setwd("/Users/mario/jobs-analysis/scripts") # Mario's Apple Macbook

# Read the original data
# Obtain functions to read and clean data.
source("R/filestuff.R")

# Read in the base job data into a data frame.
dat<-readJobsFile("../data/jobs.csv")

# The origina job ids for the test jobs - including the original
# 50 jobs + 42 jobs that gave false positive/ngative results for
# the Naive Bayesian classifier. There was also an "enhanced" job
# in this pile (AKR550).
testjobsids <- c("AIZ981", "AJA280", "AJB933", "AJC800", "AJD071",
                 "AJD448", "AJD647", "AJD722", "AJD819", "AJE088",
                 "AJF119", "AJF209", "AJF631", "AJF755", "AJF933",
                 "AJG137", "AJG140", "AJG519", "AJG605", "AJH224",
                 "AJI341", "AJI555", "AJI682", "AJL516", "AJL554",
                 "AJM703", "AJN058", "AJN409", "AJN439", "AJN523",
                 "AJO238", "AJP897", "AJR399", "AJT618", "AJU303",
                 "AJW523", "AJW636", "AJZ029", "AKA679", "AKB531",
                 "AKB914", "AKC279", "AKC302", "AKC374", "AKC484",
                 "AKC599", "AKD353", "AKD611", "AKE321", "AKE429",
                 "AKF142", "AKG102", "AKG212", "AKG345", "AKG539",
                 "AKH687", "AKH955", "AKI142", "AKI177", "AKI507",
                 "AKJ084", "AKJ250", "AKJ759", "AKK025", "AKM868",
                 "AKN442", "AKN743", "AKO091", "AKO708", "AKO738",
                 "AKP014", "AKQ081", "AKQ378", "AKR006", "AKR550",
                 "AKR991", "AKS066", "AKS118", "AKU409", "AKV103",
                 "AKV222", "AKX809", "ALA183", "ALA506", "ALA951",
                 "ALA975", "ALD798", "ALE404", "ALF731", "ALF736",
                 "ATS433")

# Second bite at the cherry - these jobs need to be classified.
# The original 50 with AKR550 replaced by AKV565.
newjobs <- c("AJC800", "AJD071", "AJD448", "AJF119", "AJF209",
            "AJF631", "AJF755", "AJF933", "AJG519", "AJH224",
            "AJI555", "AJI682", "AJL516", "AJL554", "AJM703",
            "AJN058", "AJN409", "AJN523", "AJP897", "AJT618",
            "AJU303", "AJW523", "AJW636", "AKB531", "AKD353",
            "AKD611", "AKE321", "AKE429", "AKG102", "AKG212",
            "AKG345", "AKI507", "AKJ084", "AKJ250", "AKJ759",
            "AKK025", "AKM868", "AKN442", "AKO091", "AKO708",
            "AKO738", "AKP014", "AKR006", "AKU409", "AKV103",
            "AKV222", "AKV565", "ALA183", "ALA951", "ALA975")

# Pick only the jobs from the original data for the jobs that 
# we are interestd in
jobs <- dat[dat$JobId %in% testjobsids,]
jobs2 <- dat[dat$JobId %in% newjobs,]

# Column names for csv files to be read in.
cn = c("jobid","user","class")

# Read the csv classification data from gavin
gavin <- read.csv(file="../data/gavinclass.csv",
                  stringsAsFactors = FALSE,
                  strip.white = TRUE,
                  sep=",",
                  col.names=cn)

# Only keep the unique entries (172->74). The classifier
# picked jobs at random regardless of whether it had been
# classified previously or not.
gavin<-unique(gavin)

# Originally one was still left with some conflicting duplcates. Later
# these were resolved by Gavin. Useful to have the code around.
# conflicts <- gavin[gavin$jobid %in% gavin$jobid[duplicated(gavin$jobid)],]
# print(conflicts[order(conflicts$jobid),],row.names = FALSE)
# length(conflicts$jobid)

# remove gavin's conflicting duplicates
# sel<-!(gavin$jobid %in% conflicts$jobid)
# gavin <- gavin[sel,]

# Get Mario's classification data.
mario <- readTrainingFile("../data/training1.csv")

# See what jobs are missing - this was to inform Gavin so he could
# classify the jobs.
# newjobs[newjobs %nin% gavin$jobid]

# Keep only those jobids that match gavins
# mario<-mario[mario$jobid %in% gavin$jobid,]

# Keep only those jobs that are in the 50.
mario <- mario[mario$jobid %in% newjobs,]
gavin <- gavin[gavin$jobid %in% newjobs,]

# Order the entries by the jobids
mario<-mario[order(mario$jobid),]
gavin<-gavin[order(gavin$jobid),]

# Merge the two tables
jc <- merge(mario,gavin,by="jobid")
# Write out the results.
write.csv(jc,file="mariogavin.csv",quote=FALSE,row.names=FALSE)

# Compare the results using a confusion matrix.
CrossTable(mario$class,gavin$class, prop.chisq = FALSE, prop.t = FALSE,
           prop.r = FALSE, prop.c = FALSE,
           dnn=c("mario","gavin"))

# Compare with the original classification
jobs <- jobs[jobs$JobId %in% mario$jobid,]

# We have a jobid that's not in the original data 
# (must be an enhanced job - need to do a reverse filter)
mario2<-mario[mario$jobid %in% jobs$JobId,]
gavin2<-gavin[gavin$jobid %in% jobs$JobId,]

# order the jobids
jobs <- jobs[order(jobs$JobId),]

# rename the class types
jobs$SoftwareJob<-sub("0","No",jobs$SoftwareJob)
jobs$SoftwareJob<-sub("1","Yes",jobs$SoftwareJob)

# Compare the results
CrossTable(mario2$class,jobs$SoftwareJob, prop.chisq = FALSE, prop.t = FALSE,
           prop.r = FALSE, prop.c = FALSE,
           dnn=c("mario","original classifier"))

CrossTable(gavin2$class,jobs$SoftwareJob, prop.chisq = FALSE, prop.t = FALSE,
           prop.r = FALSE, prop.c = FALSE,
           dnn=c("gavin","original classifier"))
