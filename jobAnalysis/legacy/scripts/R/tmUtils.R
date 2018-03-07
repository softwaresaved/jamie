# Text mining Utils.

# Routine to clean up a Corpus
cleanCorpus<-function(d){
  
  # A remove URLs function
  removeURLs <- function(x) gsub("(http|https)?://[.\\/[:alnum:]]*", "", x)
  
  # Remove URLs from the Corpus
  d <- tm_map(d, content_transformer(removeURLs))
  
  # A remove emails function.
  removeEmails <- function(x) gsub("[[:alnum:]]*@[.[:alnum:]]*", "", x)
  
  # Remove emails from the corpus
  d <- tm_map(d, content_transformer(removeEmails))
  
  # Perform various transformations on the text.
  d<-tm_map(d, content_transformer(tolower))     # Convert all words to lower case
  
  # Do not use the standard removePunctuation because it transforms: 
  #                   "hadoop/spark" -> "hadoopspark"
  #
  # A remove punctuation function that replaces punctuation with a space.
  #myRmPunct<- function(x) gsub("[[:punct:]]+"," ", x)
  # Modified again to not remove anything that is alphanumeric and that 
  # has a space or anything that has two ++ (for C++) or a "#" (for C#)
  myRmPunct<- function(x) gsub("[^[:alnum:][:space:]\\+{2}\\#]", " ", x)
  
  # Apply this routine to the Corpus.
  d<-tm_map(d, content_transformer(myRmPunct))
  
  # Remove stop words from the Corpus, e.g. as, the, it ...
  # To voiew the wholse set of stopwrods type: stopwords(kind="en")
  d<-tm_map(d, content_transformer(removeWords), stopwords("english"))
  
  # Some additional words to remove
  d<-tm_map(d, content_transformer(removeWords), c("will","please","s","new","based",
                                                   "school","also","contact","able","may",
                                                   "within","work","project"))
  
  # More words to remove. These seem to be common and do not help distinguish between
  # a software and non software job.
  d<-tm_map(d,content_transformer(removeWords),c("research","university","experience"))
  
  # Remove numbers from the Corpus.
  d<-tm_map(d,content_transformer(removeNumbers))
  
  # Stemming causing some problems
  #d<-tm_map(d, content_transformer(stemDocument))
  
  # Return the document to plain text otherwise you get strang errors.
  # Stemming maps: stems, stemming, stemmed -> stem, i.e. it's root.
  # This does not appear to be needed if the content transformers are used.
  # d<-tm_map(d, content_transformer(PlainTextDocument))
  
  # Remove excess white spaces.
  d<-tm_map(d, content_transformer(stripWhitespace))
  
  return(d)
}

