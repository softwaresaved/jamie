#!/usr/bin/env Rscript
#
# Trying to use text mining to look at the jobs data.
#

# Libraries that may be required
# Use sessionInfo() to see what packages are already uploaded.

library(NLP)            # Natural Language Processing, required by tm
library(tm)             # R text mining package
library(RColorBrewer)   # Required by wordcloud
library(wordcloud)      # Produces pretty word clouds
library(SnowballC)      # For stemming if used
library(ggplot2)        # Plot library
library(RWeka)          # Link to the Java Weka package
library(pander)         # Data can be printed for wiki consumption
library(slam)           # Algorithms for sparse matrices
library(e1071)          # Naive Bayes
library(wordcloud)      # For producing word clouds
library(gmodels)        # Need this to get the CrossTables function
#library(klaR)           # Naive Bayes - need to establish which is more suitable
#library(ROCR)           # Visualizing classifier

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

# aide a memoir: duplicated, intersect,setdiff

# Read the data into a data frame (dat).
dat<-readJobsFile(file="../data/jobs.csv")

# Read the jobids that are to constitute the training/test sets.
classified <- readTrainingFile("../data/training2.csv")

# Read in data that has not got the "Maybe"s->"Yes"s for comparison.
classified2 <- readTrainingFile("../data/training1.csv")

# Jobs classified as "Software Engineering" jobs according to the
# the job subject
sofengjobids <- read.table("../data/SoftEngJobIDs.txt",
                           stringsAsFactors = FALSE,
                           col.names = c("id"),
                           header = FALSE)

# Assume all of these to be software jobs.
sofengjobids <- cbind(sofengjobids,
                       class=vector(mode="logical",
                                    length = length(sofengjobids$id)))
sofengjobids$class <- TRUE

# Convert the class to be a factor as we are using a categorical
# variable.
classified$class   <- factor(classified$class)
classified2$class  <- factor(classified2$class)
sofengjobids$class <- factor(sofengjobids$class)

# Keep only the training/test set jobs tat are not in the Corpus. 
# This will happen because enhanced jobs are not incorporated but 
# can be classified.
classified<-classified[classified$jobid %in% dat$JobId,]
classified2<-classified2[classified2$jobid %in% dat$JobId,]
sofengjobids <- sofengjobids[sofengjobids$id %in% dat$JobId,]

# Check whether we have duplicated entries - need to remove these.
n<-classified$jobid[duplicated(classified$jobid)]
if(length(n)> 0){
  print(paste0("Have the following replicated classifed jobs: ",n))
}

# Create a set of training & test jobs.
tdat<-dat[dat$JobId %in% classified$jobid,]

# Merge jobs information and their classification (for ease).
tdat<-merge(tdat,classified,by.x="JobId",by.y="jobid")

# Second test set made up from the "Software Engineering" job ids.
tdat2 <- dat[dat$JobId %in% sofengjobids$id,]

# http://www3.nd.edu/~steve/computing_with_data/20_text_mining/text_mining_example.html#/
# Divide the jobs into 75% training set and a 25% test set.
n      <- length(tdat$JobId)        # Number of jobs
ntrain <- as.integer(0.75*n)        # Number of training jobs (75%)
ntest  <- n - ntrain                # Remainder as test jobs

# Create the training and testing jobs data frame.
set.seed(123456)                    # Get a level of reproducibility
nsamp<-sample(nrow(tdat),ntrain)    # Sample the jobs
trainjobs<-tdat[nsamp,]             # Get a training set of jobs
testjobs<-tdat[-nsamp,]             # Use the rest as a test set

trainclass2 <- classified2[nsamp,]
testclass2  <- classified2[-nsamp,]

# Print diagnostic a message.
print(paste0("Using ",ntrain," jobs out of ",n," for training (with ",
             sum(trainjobs$class=="Yes")," software jobs) and ",
             ntest," jobs (with ",sum(testjobs$class=="Yes"),
             " software jobs) for testing."))

# Check proportions of software jobs are similar for both classes of jobs.
prop.table(table(trainjobs$class,dnn=list("\nTraining software jobs:\n")))
prop.table(table(testjobs$class,dnn=list("\nTest software jobs:\n")))

# Create a training and test Corpus. Only using the job name (title)
# and job description. In theory other elements of the job data could
# be used.
train_raw<-paste0(trainjobs$Name,". ",trainjobs$Description)
traincp <- Corpus(VectorSource(train_raw))

test_raw<-paste0(testjobs$Name,". ",testjobs$Description)
testcp  <- Corpus(VectorSource(test_raw))

test2_raw<-paste0(tdat2$Name,". ",tdat2$Description)
testcp2 <- Corpus(VectorSource(test2_raw))

# Clean the data - removes multiple spaces, punctuation, numbers, stopwords, etc.
traincp <- cleanCorpus(traincp)
testcp  <- cleanCorpus(testcp)
testcp2 <- cleanCorpus(testcp2)

# Associate the jobid with the document metadata
meta(traincp,type="local",tag="id") <- traincp$JobId
meta(testcp,type="local",tag="id")  <- testcp$JobId
meta(testcp2,type="local",tag="id") <- testcp2$JobId

# Create a document term matrix for the training and test data.
# Could reduce the size of the Document Term Matrix (dtm) by adding
# ",minDocFrequency=10" to the control list, e.g. the term must
# appear at least N times in order for it to be considered. This appears
# to have no impact(!).
traindtm <- DocumentTermMatrix(traincp, 
                               control=list(wordLengths=c(1,Inf)))
testdtm  <- DocumentTermMatrix(testcp, 
                               control=list(wordLengths=c(1,Inf)))
testdtm2 <- DocumentTermMatrix(testcp2, 
                               control=list(wordLengths=c(1,Inf)))

# The dtm consists of a sparse matrix with each job constituting a
# row and the terms (or words) along the top of the columns. The 
# entries then constitute the number of time each term is found in
# in a job. For the classifier we do not need to know the counts
# so we convert each term into a 1 if greater than zero. Create 
# a function to do this:
convert_counts <- function(x) {
  x <- ifelse(x > 0, 1, 0)
  x <- factor(x, levels = c(0, 1), labels = c("No", "yes"))
  return(x)
}

# Now apply this to each dtm. MARGIN=2 means that we are 
# applying it over the columns. A 1 would indicate rows.
trnjobs <- apply(traindtm,MARGIN = 2,convert_counts)
tstjobs <- apply(testdtm,MARGIN = 2,convert_counts)
tstjobs2 <- apply(testdtm2,MARGIN = 2,convert_counts)

# Train the classifier
model <- naiveBayes(trnjobs,trainjobs$class,laplace = 0.125)

# Test the classifier
results  <- predict(model,tstjobs)
results2 <- predict(model,tstjobs2)

# Evaluate the predictions by producing a confusion matrix
CrossTable(results,testjobs$class, prop.chisq = FALSE, prop.t = FALSE,
           prop.r = FALSE, prop.c = FALSE,
           dnn=c("predicted","actual"))

CrossTable(results2,sofengjobids$class, prop.chisq = FALSE, prop.t = FALSE,
           prop.r = FALSE, prop.c = FALSE,
           dnn=c("predicted","actual"))

# Create a data frame with the results
CrossTable(results,testclass2$class, prop.chisq = FALSE, prop.t = FALSE,
           prop.r = FALSE, prop.c = FALSE,
           dnn=c("predicted","actual"))

# Find out the job ids of jobs that have been misclassified
# Attach the predicted jobs columns
testjobs<-cbind(testjobs,pred=results)

# Job ids for false-negatives
falngv <- testjobs$JobId[testjobs$pre=="No"&testjobs$class=="Yes"]
orgclass1 <- classified2$class[classified2$jobid %in% falngv]
table(orgclass1)

# Job ids for false positives
falpov <- testjobs$JobId[testjobs$pre=="Yes"&testjobs$class=="No"]
orgclass2 <- classified2$class[classified2$jobid %in% falpov]
table(orgclass2)

################################
# Aside: looking at word clouds

# View the words in the training corpus
wordcloud(traincp,min.freq = 92,random.order = FALSE)

# See if we can see a word difference in the software jobs data 
# set and the non-software jobs dataset by visualising using a 
# wordcloud. Select the data:
sw<-subset(traincp,trainjobs$class=="1")
nsw<-subset(traincp,trainjobs$class=="0")

# Print the wordclouds.
wordcloud(sw,min.freq = 40,random.order = FALSE)
wordcloud(nsw,min.freq = 92,random.order = FALSE)

