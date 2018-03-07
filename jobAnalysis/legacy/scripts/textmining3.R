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
datbase<-readJobsFile(file="../data/jobs.csv")

# Create a Corpus that only has IT and computer Science subjects.
dat<-datbase[(grepl("Computer Science",datbase$Subject)|grepl("IT",datbase$Subject))&
            grepl("fortran",paste(datbase$Name,datbase$Description),ignore.case = TRUE),]

###########################################################################
# Text mining
#
# Unlike the other text mining file this starts from the CSV content as opposed
# to trying to do it through the raw job files themselves.
#

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
dtm <- DocumentTermMatrix(myc)

# Query the dtm
dim(dtm)      # Returns number of docs x number of terms
nDocs(dtm)    # Returns the number of docs.
nTerms(dtm)   # Returns the number of terms.
Docs(dtm)     # Returns the list of document names in the corpus (index in this case)
Term(dtm)     # Returns a list of terms

# Term frequency
tf<-col_sums(dtm)

# Add a wordcloud
wordcloud(names(tf),as.numeric(tf),random.order=FALSE, rot.per=0.35, 
          use.r.layout=FALSE, colors=brewer.pal(8, "Dark2"))

########################################################################
# Hierarchical cluster analysis - cluster documents together according
# to their similarity or distance spearation. This does not scale - 
# suitable for relatively small data sets.
########################################################################

# Calculate the separation between documents.
d<-dist(dtm)

# Do the hierarchical data clustering
hdc<-hclust(d,method="ward.D")

# Visualise the results as various dendograms.
plot(hdc)
plot(hdc,hang=-1)           # Level the labels
plot(hdc,type="triangle")

# Analyses of Phylogenetics and Evolution provides you with ways of plotting
# the dendograms
library(ape)
plot(as.phylo(hdc), cex = 0.9, label.offset = 1)

plot(as.phylo(hdc), type = "unrooted")

plot(as.phylo(hdc), type = "fan")

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

# Generate a document term matrix using Tf-Idf weighing
dtm2<- DocumentTermMatrix(myc, control = list(weighting = weightTfIdf,
                                              wordLengths=c(1,Inf)))

# Plot the weight derived from the term frequency * inverse document frequency
# against the term frequency.
p<-data.frame(w=sort(col_sums(weightTfIdf(dtm,normalize = FALSE)),decreasing=TRUE),
              f=sort(col_sums(dtm),decreasing = TRUE),stringsAsFactors = FALSE)

qplot(data=p,x=w,y=f,geom="point") + 
  xlab("term frequency-inverse ddocument frequency") + ylab("term frequency")

# Number of terms per documet
docs<-col_sums(dtm>0)

# Terms
terms<-col_sums(dtm)

# term frequence - document inverse frequency
tfidf2<-col_sums(weightTfIdf(dtm,normalize = TRUE))

# calculate tf-idf for each term
tfidf <-  tapply(dtm$v/row_sums(dtm)[dtm$i], dtm$j, mean) * 
          log2(nDocs(dtm)/col_sums(dtm > 0))

# select columns with tfidf > median
dtm <- dtm[, tfidf >= median(tfidf)]

#select rows with rowsum > 0
dtm <- dtm[row_sums(dtm) > 0,]

# report reduced dimension
dim(dtm2)

# set number of topics to extract
k <- 5
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
terms(TM[["VEM"]], 6)

#######################################################################################
# From:
# http://stackoverflow.com/questions/14267199/math-of-tmfindassocs-how-does-this-function-work
# u is a term document matrix (transpose of a DTM)
# term is your term
# corlimit is a value -1 to 1

findAssocsBig <- function(u, term, corlimit){
  suppressWarnings(x.cor <-  gamlr::corr(t(u[ !u$dimnames$Terms == term, ]),        
                                         as.matrix(t(u[  u$dimnames$Terms == term, ]))  ))  
  x <- sort(round(x.cor[(x.cor[, term] > corlimit), ], 2), decreasing = TRUE)
  return(x)
}
#######################################################################################

#####################################
# Example to see how findAssocs work

# How findAsspcs os calculated example from:
# https://stat.ethz.ch/pipermail/r-help/2012-July/319027.html

# Create a Corpus
data <-  c("word1", "word1 word2","word1 word2 word3","word1 word2 word3 word4",
           "word1 word2 word3 word4 word5")
frame <-  data.frame(data)
frame
test <-  Corpus(DataframeSource(frame))

# Create the dtm
dtm <-  DocumentTermMatrix(test)

# Inspect the dtm
as.matrix(dtm)
# or
inspect(dtm)

# Test case
findAssocs(dtm, "word2", 0.1)

# Correlation word2 with word3
cor(c(0,1,1,1,1),c(0,0,1,1,1))

# Correlation word2 with word4
cor(c(0,1,1,1,1),c(0,0,0,1,1))

# Correlation word2 with word5
cor(c(0,1,1,1,1),c(0,0,0,0,1))

# Correlation word1 with word5
cor(c(1,1,1,1,1),c(0,0,0,0,1))

cor(seq(1,10),seq(1,10))
cor(seq(1,10),seq(10,1,-1))

