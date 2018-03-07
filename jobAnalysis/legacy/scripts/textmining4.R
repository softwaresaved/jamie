#!/usr/bin/env Rscript
#
# Trying to use text mining to look at the jobs data.
#

# Libraries that may be required
# If missing a library you can use: 
#
#  install.packages("MissingLibrary")
#
# at the R prompt to install it.
#
library(NLP)            # Natural Language Processing, required by tm
library(tm)             # R text mining package
library(RColorBrewer)   # Required by wordcloud
library(wordcloud)      # Produces pretty word clouds
library(SnowballC)      # For stemming if used
library(ggplot2)        # Plot library
library(RWeka)          # Link to the Java Weka package
library(pander)         # Data can be printed for wiki consumption
library(slam)           # Algorithms for sparse matrices
library(topicmodels)

# Possible classifiers that could be used:
#library(class) # Sec 5.3 of Text Mining Infrastructure in R.

####################
# Read in the data #
####################

# Set the working directory to be where this file is located - you can
# add a line for your directory based on your hostname. This specific 
# directory is needed as files are found by a relative path.

# Find out the hostname.
hostname<-Sys.info()["nodename"]

# Set the working directory.
if(hostname == "mbp-ma.local"){
  setwd("/Users/mario/jobs-analysis/scripts")
}else{
  print("You need to set your current working directory.")
}

# Load in functions to read and clean the data.
source("R/filestuff.R")

# Load text mining utils.
source("R/tmUtils.R")

# Read the data into a "dat" data frame.
dat<-readJobsFile(file="../data/jobs.csv")

# Create the Corpus - join the job name (or title) with the 
# job description
myc<-Corpus(VectorSource(paste0(dat$Name,". ",dat$Description)))

myc2<-Corpus(VectorSource(paste0(dat$Name,". ",dat$Description)))

# Transform the data
myc <- cleanCorpus(myc)

# Associate the jobid with the document metadata
# This association can take a bit of time so 
# DON'T DO IT unless you have to.
# Types can be:
# corpus  - corpus specific metadata.
# indexed - document specific but stored in the corpus as 
#           a data frame.
# local   - document specific stored with each document.
meta(myc,type="local",tag="id")<-dat$JobId

# Create a document term matrix - the rows each represent a document 
# (i.e. a job in this case) and the columns each give the number of 
# times that word is found in that document. Needless to say this will 
# usually result in a very large sparse matrix. Can also prodcue a 
# TermDocumentMatrix which is just the transpose of the dtm.
dtm <- DocumentTermMatrix(myc, control=list(wordLengths=c(1,Inf)))

# Query the dtm
dim(dtm)      # Returns number of docs x number of terms
nDocs(dtm)    # Returns the number of docs.
nTerms(dtm)   # Returns the number of terms.
Docs(dtm)     # Returns the list of document names in the corpus (index in this case)
Term(dtm)     # Returns a list of terms

###############################################################
# Looking at Topic modelling from:
#
#  www.richardtwatson.com/dm6e/Reader/slides/pptx/chapt16.pptx
#

# Use the weightTFIdf to weigh the terms as opposed to the term frequency 
# by itself that dan skew the results. 
#
# weightTFIdf = TermFrequency * log2(NumberOfDocument/DocumentsTermFoundIn)
#

# calculate tf-idf for each term
tfidf <-  tapply(dtm$v/row_sums(dtm)[dtm$i], dtm$j, mean) * 
          log2(nDocs(dtm)/col_sums(dtm > 0))

# select columns with tfidf > median
dtm <- dtm[, tfidf >= median(tfidf)]

#select rows with rowsum > 0
dtm <- dtm[row_sums(dtm) > 0,]

# report reduced dimension
dim(dtm)

# set number of topics to extract
k <- 10 # 5 originally
SEED <- 2010

# try multiple methods – takes a while for a big corpus
TM <- list(VEM = LDA(dtm, k = k, control = list(seed = SEED)),  
           VEM_fixed = LDA(dtm, k = k, 
                           control = list(estimate.alpha = FALSE, seed = SEED)), 
           Gibbs = LDA(dtm, k = k, method = "Gibbs", 
                       control = list(seed = SEED, burnin = 1000, thin = 100, 
                                      iter = 1000)), 
           CTM = CTM(dtm, k = k,control = list(seed = SEED, var = list(tol = 10^-3), 
                                               em = list(tol = 10^-3))))

topics(TM[["VEM"]], 1)
terms(TM[["VEM"]],1)
topics(TM[["VEM"]], 2)
topics(TM[["VEM"]], 3)
topics(TM[["VEM"]], 4)
terms(TM[["VEM"]], 4)
terms(TM[["VEM"]], 100)

###########################################################
# Bit of fun - readability score for each job.
# This takes too long to run for the all the jobs.
library(koRpus)
job<-paste0(dat$Name[1:100]," ",dat$Description[1:100])
for(i in seq(1,10)){
  tagged.job<-tokenize(as.character(job[i]),format="obj",lan="en")
  print(readability(tagged.job,"Flesch.Kincaid",hyphen=NULL,force.lang="en"))
}



