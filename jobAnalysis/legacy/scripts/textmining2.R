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

###########################################################################
# Text mining
#
# Unlike the other text mining file this starts from the CSV content as opposed
# to trying to do it through the raw job files themselves.
#

# Create the Corpus - join the job name (or title) with the 
# job description
myc<-Corpus(VectorSource(paste0(dat$Name,". ",dat$Description)))

# To view the content of a particular document need to use:
# as.character(myc[[1]]). Use nchar() to count characters.
j<-as.character(myc[[1]]) # Reference job to check on the changes

# List available transformations.
getTransformations()

# Clean the data up
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
meta(myc,type="local",tag="salMin")<-dat$SalaryMin
meta(myc,type="local",tag="salMax")<-dat$SalaryMax
meta(myc,type="local",tag="Role")<-dat$Role
meta(myc,type="local",tag="Subject")<-dat$Subject
meta(myc,type="local",tag="Location")<-dat$Location
meta(myc,type="local",tag="Location2")<-dat$Location2
meta(myc,type="local",tag="placedDate")<-dat$PlacedOn
meta(myc,type="local",tag="closingDate")<-dat$Closes

# View the metadata for the first document.
meta(myc[[1]])

# Inspect a summary first six documents.
head(summary(myc))

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

# Space being used up by various objects
format(object.size(myc),units="Mb")
format(object.size(dtm),units="Mb")

# Find frequency of each term. Gives a vector with the occurrences of a
# term across the corpus. Can dereference by using nterm["fortran"] to
# see how often fortran appears in the Corpus.
nterm<-col_sums(dtm)

# Number of documents a term appears in.
termindocs<-col_sums(dtm>0)

# Number of terms in a document
numterms<-row_sums(dtm>0)
qplot(numterms,geom="bar",bin=1,xlim=c(0,300),
      col=I("red"), xlab="Number of Terms",ylab="Frequency")

# Inverse document
idtf<-weightTfIdf(dtm, normalize = TRUE)

# Inverse document term frequencey
iterm<-col_sums(idtf)

# Numer of terms (words) found across the corpus (after cleaning)
qplot(row_sums(dtm),geom="bar",bin=1,xlim=c(0,500),
      col=I("red"), xlab="Number of Words",ylab="Number of Jobs")

qplot(col_sums(dtm),geom="bar",bin=1,xlim=c(0,50),
      col=I("red"), xlab="Frequency of Terms",ylab="Number of Jobs")

# Can remove sparse terms from the dtm. It removes all terms that have
# a "sparse" value
# Not sure we want to do this as it could get rid of the words
# we want. However, if we do not we end up with a dtm that is far
# too large.
#        sparse  ndocs   nterms  remove terms that do not appear in at least
#  dtm -         62287    77164
# rdtm -  0.1    62287        1   90% of the docs
# rdtm -  0.5    62287        9   50% of the docs
# rdtm -  0.75   62287       77   25% of the docs
# rdtm -  0.9    62287      270   10% of the docs
# rdtm -  0.99   62287     2021    1% of the docs
# rdtm -  0.999  62287     7016    0.1% of the docs
# rdtm -  0.9999 62287    21305    0.01% of the docs
#
# i.e. 1 - (Occurrence of term/Total number of terms) <= sparse
#
rdtm<-removeSparseTerms(dtm,sparse=0.999)
dim(rdtm)

# Can create a smaller document term matrix where terms that appear less 
# or more times than a set of bounds bound are discarded.
sdtm<-DocumentTermMatrix(myc,control=list(bounds=list(global=c(20,Inf))))
dim(sdtm)

# Find terms that have more than 5000 occurrences
#fw<-findFreqTerms(dtm,5000)
fw<-findFreqTerms(dtm)
ifw<-findFreqTerms(idtf)

# Make a pretty picture - use the most common word in the corpus.
# The dtm is too big to do this with.
m<-as.matrix(sdtm) # Does not work as dtm is too large 
wc<-sort(colSums(m),decreasing=TRUE)
wc2<-head(wc,500)                     # Only show the top 500 words
wordcloud(names(wc2),freq=wc2,colors=rainbow(24))

m<-as.matrix(rdtm) # Does not work as dtm is too large 
wc<-sort(colSums(m),decreasing=TRUE)
wc2<-head(wc,500)                     # Only show the top 500 words
wordcloud(names(wc2),freq=wc2,colors=rainbow(24))

m<-as.matrix(head(wc,15))
colnames(m)<-c("Word occurrence")
pander(m,style="rmarkdown",justify=c("left","left"))

# Construct a reg expression for words currently used to identify s/w jobs.
sfw_words<-paste("software developer",
                 "coding",
                 "coder",
                 "research software engineer",
                 "software engineer",
                 "programming",
                 "programme",
                 "fortran",
                 "C\\+\\+",
                 "java",
                 "javascript",
                 "matlab",
                 "python",
                 "perl",
                 sep="|")

sfwords = c("software developer",
             "coding",
             "coder",
             "research software engineer",
             "software engineer",
             "programming",
             "programme",
             "fortran",
             "c\\+\\+",
             "java",
             "javascript",
             "matlab",
             "python",
             "perl")

# Find the correlations
crs<-findAssocs(dtm,sfwords,corlimit = 0.1)

findAssocs(dtm,"c++",corlimit = 0.1)

# An alternative for findAssocs
# http://stackoverflow.com/questions/14267199/math-of-tmfindassocs-how-does-this-function-work

findAssocs(dtm,terms=c("coding"),0.1)
findAssocs(dtm,terms=c("coder"),0.1)
findAssocs(dtm,terms=c("cuda"),0.1)
findAssocs(dtm,terms=c("developer"),0.1)
findAssocs(dtm,terms=c("engineer"),0.1)
findAssocs(dtm,terms=c("linux"),0.1)
findAssocs(dtm,terms=c("openmp"),0.4)
findAssocs(dtm,terms=c("software"),0.1)
findAssocs(dtm,terms=c("programme"),0.1)
findAssocs(dtm,terms=c("program"),0.1)
findAssocs(dtm,terms=c("unix"),0.1)

# Other languages that should be there but will probably give a lot of false
# positives: C, R

# c++,c, c# and R will not work as punctuation has been removed and 
# not sure if a single letter is maintained in the Corpus
langs <- c(
  "css",
  "cuda",
  "fortran",
  "genstat",
  "groovy",
  "hadoop",
  "haskell",
  "html",
  "java",
  "javascript",
  "jquery",
  "julia",
  "linux",
  "lua",
  "matlab",
  "mpi",
  "nosql",
  "openmp",
  "pascal",
  "perl",
  "php",
  "python",
  "ruby",
  "sas",
  "scala",
  "spark",
  "spss",
  "stata"
)

# Hierarchical data clustering - the calculation of the distance
# matrix does not work unless the dtm is pretty small and the 
# hierachical clustering fails even then ...
# Select only those documents that contain an instance of a lang.
s<-grepl(paste0(langs,collapse="|"),paste(dat$Name,dat$Description))
# Filter down the Corpus
mycl<-myc[s]
# Size of the orginal document term matrix
dim(dtm)
# [1] 62288 77168
# Create a new document term matrix
mdtm<-DocumentTermMatrix(mycl)
dim(mdtm)
# [1] 10059  7854
# Remove any elements that are less than 1% populated
mdtm<-removeSparseTerms(mdtm,sparse=0.99)
dim(mdtm)
#[1] 10059  2279
# Calculate the separation.
d<-dist(mdtm)
#> length(d)
#[1] 50586711
# Do the hierarchical data clustering
hdc<-hclust(d,method="ward.D")
# Visualise the results
plot(hdc)

# Redirect output
sink(file="assoc.txt")

# Loop over the languages
for (l in langs){ 
  
  #print(paste("Processing:",l))
  
  # Find the associations, returns this as a list.
  as<-findAssocs(dtm,l,0.1)
  
  # Convert the list to a matrix (for pander)
  m<-as.matrix(unlist(as))
  
  # Only consider non-zero associations
  if(length(m)>0){

    # Remove the "term." in the rownames
    rownames(m)<-gsub(paste0(l,"."),"",rownames(m))
    
    # Find the actual frequency of each of the terms
    ml<-list()
    for(n in rownames(m)){
      #print(n)
      ml[n]<-ifelse(length(nterm[n == names(nterm)])>0,nterm[n == names(nterm)],0)
    }
    m2<-as.matrix(unlist(ml))

    # Combine the two matrices
    m<-cbind(m,m2)
    
    # Add a name to each column
    colnames(m)<-c(paste0(l," (",nterm[nterm=l],")"," associations"),"Occurrences")
     
    # Print the result as a table.
    # In case we no longer want to emphasize columns: emphasize.rownames = FALSE
    # style can be rmarkdown, grid, markdown
    pander(m,style="rmarkdown",justify=c("left","left","left"))

    # Create a wordcloud
    png(file=paste0(l,"-word.png"))
    wordcloud(rownames(m2),freq=as.numeric(m2),colors = rainbow(24))
    dev.off()
  }
}

# Close the redirection.
sink()

# find associations
as<-findAssocs(dtm,terms=langs,0.4)

findAssocs(dtm,terms=c("fortran"),0.2)
findAssocs(dtm,terms=c("scala"),0.2)
findAssocs(dtm,terms=c("java"),0.2)
findAssocs(dtm,terms=c("spss"),0.2)
findAssocs(dtm,terms=c("html"),0.2)
findAssocs(dtm,terms=c("css"),0.2)
findAssocs(dtm,terms=c("haskell"),0.2)
findAssocs(dtm,terms=c("cuda"),0.2)

disc<-c("software",
        "program",
        "developer",
        "programmer",
        "research",
        "engineer")

findAssocs(dtm,terms=disc,corlimit = 0.4)

# Inspect an element
as[["fotran"]]

# Criptic way of obtaining a word cloud
term = "java" # "javascript"
wordcloud(names(as[[term]]),feq=as.numeric(as[[term]]*100),colors=rainbow(24))

# Document cluster
dtm_tfxidf <- weightTfIdf(dtm)
inspect(dtm_tfxidf[1:10, 5001:5010])
m <- as.matrix(dtm_tfxidf)
rownames(m) <- 1:nrow(m)



