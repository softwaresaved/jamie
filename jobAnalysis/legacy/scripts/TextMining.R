#!/usr/bin/env Rscript
##################################################################
# Trying out the R tm (text mining) package. 
# Experimenting here so not everything will work well.
#
# Need to install if not already there: 
#
#            install.package("NLP")  # Natural language processing, a pre-requisite
#            install.package("tm")   # The text mining package
#            install.package("tm.plugin.webmining")
#
# Note on a Mac it seems to download packages. To install them you have to go to 
# the directory where the file has been downloaded and then do:
#
# R CMD install PackageFileName
#
# where PackageFileName is clearly the actual package file name.

# Load the text miniming package (tm)
library(NLP)
library(tm)

# Can use this to strip out html tags (not used at the moment)
#library(tm.plugin.webmining)

# Session info returns useful information about the packages being
# used.
sessionInfo()

# Adapting things from:
#
#   o http://onepager.togaware.com/TextMiningO.pdf
#   o http://cran.r-project.org/web/packages/tm.plugin.webmining/vignettes/ShortIntro.pdf
#
# Create a Corpus (collection of text documents, in this case each
# document corresponds to a job). 

# Before proceeding make sure the working directory is set (see above) 
# corresponding to the parent directory of the jobs subdirectory.

# Set the working directory (machine dependent)
setwd("/Users/mario/jobs-analysis/scripts")

# List all available data sources 
getSources()

# List available readers
getReaders()

# Create a directory path to the jobs
#JobsPath<-file.path(".","jobs") 
JobsPath<-file.path(".","jobs1000") 

# Create a data source.
JobSource<-DirSource(directory=JobsPath,
                     encoding="UTF-8",
                     pattern=NULL,
                     recursive=FALSE,
                     ignore.case=FALSE,
                     mode="text")

# Create the Corpus
JobsCorpus<-Corpus(JobSource, 
                   readerControl = list(reader = JobSource$DefaultReader, 
                                        language = "en"))
                   
# Get information about the Corpus - VCorpus is a Volatile Corpus.
class(JobsCorpus)

# Get information about the first document
class(JobsCorpus[[1]])

# [N] gives you the Nth position in the Corpora
JobsCorpus[1]

# [[N]] gives you the Nth document in the Corpora
JobsCorpus[[1]]

# Access Document Metadata
meta(JobsCorpus[[1]])
inspect(JobsCorpus[1])   # Produces same result

# View the full contents of document, or job,  1
inspect(JobsCorpus[1])

# Do the same thing for jobs 1-2
inspect(JobsCorpus[1:2])

# Provide a conise overview of job 1
print(JobsCorpus[1])

# Documents have html tags can remove these through a single transformations on the docs
# Remove html (from: http://www.r-bloggers.com/htmltotext-extracting-text-from-html-via-xpath/)
# Patther to use to capture html elements
#pattern <- "</?\\w+((\\s+\\w+(\\s*=\\s*(?:\".*?\"|'.*?'|[^'\">\\s]+))?)+\\s*|\\s*)/?>"

# Go over all the documents and remove the html tags. 
# To execute multiple lines in RStudio highlight the code that you want to execute
# and then press Cnt-Enter at the end.
# Should really use tm_map to apply a transformation to the whole corpus.
for(j in seq(JobsCorpus))
{
  #JobsCorpus[[j]]<-gsub(pattern, "\\1", JobsCorpus[j])
  JobsCorpus[[j]]<-gsub("<.*?>", "\\1", JobsCorpus[j])
  
}

# Trying to follow:
#
# https://deltadna.com/blog/text-mining-in-r-for-term-frequency/
#

# Remove punctuation marks from a text document.
JobsCorpus<-tm_map(JobsCorpus, removePunctuation)

# Strip extra whitespace from a text document. 
# Multiple whitespace characters are collapsed to a single blank.
JobsCorpus<-tm_map(JobsCorpus, stripWhitespace)

# Remove stop words from a text document. Type: stopword("english") to
# see what these are.
JobsCorpus<-tm_map(JobsCorpus, removeWords, stopwords("english"))

# Deal with stemming
JobsCorpus<-tm_map(JobsCorpus, stemDocument)

# Need this otherwise get a strange error.
JobsCorpus<-tm_map(JobsCorpus, PlainTextDocument)

#summary(JobsCorpus)
#inspect(JobsCorpus[16])

# Create a document term matrix
dtm <- DocumentTermMatrix(JobsCorpus, control=list(wordLengths=c(1,Inf)))

# Term document matrix (transpose of the above)
tdm <- TermDocumentMatrix(JobsCorpus)

# Find terms that have more than 50000 occurrences
findFreqTerms(dtm,50000)

# find associations
findAssocs(dtm,"fortran",0.5)

library(wordcloud)

dtm2<-as.matrix(dtm)

dictionary<-c(
              "asp.net",
              "c",
              "c#",
              "c++",
              "fortran",
              "genstat",
              "hadoop",
              "html",
              "java",
              "javascript",
              "jquery",
              "julia",
              "matlab",
              "nosql",
              "perl",
              "php",
              "python",
              "r",
              "sas",
              "spark",
              "spss",
              "stata",
              "sql"
             )

complangs <- DocumentTermMatrix(JobsCorpus,list(dictionary))
inspect(complangs)
