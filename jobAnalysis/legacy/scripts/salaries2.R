# Look at the semantical construction of the salary field to see
# what words are used. The intent is to try and separate salaries 
# that are not annual.

library(NLP)            # Natural Language Processing, required by tm
library(tm)             # R text mining package
library(RColorBrewer)   # Required by wordcloud
library(wordcloud)      # Produces pretty word clouds
library(SnowballC)      # For stemming if used
library(ggplot2)        # Plot library
library(RWeka)          # Link to the Java Weka package
library(pander)         # Data can be printed for wiki consumption
library(slam)           # Algorithms for sparse matrices
library(gmodels)        # Need this to get the CrossTables function
library(scales)         # Want this for the percent function

###############
# Read in data.
###############

# Need some routines from this R files.
source("R/filestuff.R")
source("R/tmUtils.R")

# Load up the job information.
dat<-readJobsFile("../data/jobs.csv")

################################################
# Create a wordcloud of words used for salaries
################################################

# Extract the salary field.
sal<-dat$Salary

# Create a corpus from these fields.
csal<-Corpus(VectorSource(sal))

# Remove stop words, emails, urls, etc.
csal<-cleanCorpus(csal)

# Create a document term matrix.
dtm <- DocumentTermMatrix(csal, control=list(wordLengths=c(1,Inf)))

# Sum of the terms.
numterms <- col_sums(dtm)

# Convert to a matrix and sort count in descending numerical order
m <- as.matrix(sort(numterms,decreasing = TRUE))

# Name the column
colnames(m) <- c("Occurrences")

# print a wiki friendly table
pander(head(m,10),
       style="grid",
       plain.ascii = TRUE,
       justify=c("left","left"),
       split.table=Inf)

# Create a colour palette
pal2 <- brewer.pal(8,"Dark2")

# Create a word cloud to see what there is.
wordcloud(csal,min.freq = 25,random.order = FALSE,colors = pal2,scale = c(8,0.5))

##############################
# Look at salary distributions
##############################

# create a new frame
sub2<-data.frame(id=dat$JobId,
                 sub=dat$Subject,
                 sal=dat$Salary,
                 min=dat$SalaryMin,
                 max=dat$SalaryMax,
                 loc=dat$Location,
                 loc2=dat$Location2,
                 con=dat$Contract,
                 uk=dat$InUK,
                 sfw=dat$SoftwareJob,
                 hours=dat$Hours,
                 qualification=dat$QualifcationType,
                 funding=dat$FundingFor,
                 stringsAsFactors = FALSE)

# Process the salaries - remove pound sign and commas
sub2$min<-gsub(" |£|,","",sub2$min)
sub2$max<-gsub(" |£|,","",sub2$max)

# Need to remove unspecified or negotiable salaries
sub2<-sub2[-grep("Unspecified|Negotiable",sub2$min),]

# Convert salaries to numbers
sub2$min<-as.numeric(sub2$min)
sub2$max<-as.numeric(sub2$max)

# Plot the salary min vs max
ggplot(data=sub2,aes(x=min,y=max,color=hours)) + 
       geom_point(size=2,alpha=0.25)+ 
       labs(x="Salary Minimum",y="Salary Maximum")

# Total number of jobs
n <- length(sub2$id)
paste0("This is ",n," (",percent(n/length(dat$JobId)),") of the original.")

# Look at the number of full/part time jobs.
m <- as.matrix(table(sub2$hours))
m <- cbind(m,percent(m/n))
colnames(m)<-c("Number of Jobs", "Percent of Jobs")

# Look at the composition of jobs
pander(head(m),style="grid", 
       plain.ascii = TRUE,
       justify=c("left","right","right"),split.table=Inf)

# Look at the contracts (permanent/temporary) for the jobs
m<-as.matrix(table(sub2$con))
m <- cbind(m,percent(m/n))
colnames(m)<-c("Number of Jobs", "Percent of Jobs")

pander(head(m),style="grid", 
       plain.ascii = TRUE,
       justify=c("left","right","right"),split.table=Inf)

# Plot the salary min vs max with contract colouring of points.
ggplot(data=sub2,aes(x=min,y=max,color=con)) + 
  geom_point(size=2,alpha=0.25)+ 
  labs(x="Salary Minimum",y="Salary Maximum")

# Compare and contrast contract vs hours
CrossTable(sub2$con,sub2$hours, prop.chisq = FALSE, prop.t = FALSE,
           prop.r = FALSE, prop.c = FALSE,
           dnn=c("contract","hours"))

# Plot a tile diagram.
ggplot(data=sub2,aes(x=factor(hours),y=factor(con))) +
  geom_tile() + stat_bin2d() +
  labs(y="Contract",x="Hours")

# Take only jobs that have "Part Time" specified, i.e. there are
# some "Full Time, Part Time" jobs.
sub<-sub2[grepl("Part Time",sub2$hours ),]

# Plot the salary min vs max for part time jobs
ggplot(data=sub,aes(x=min,y=max,color=hours)) + 
       geom_point(size=2,alpha=0.25)+ 
       labs(x="Salary Minimum",y="Salary Maximum")

# Get some stats on the contracts.
summary(sub2$max[sub2$con=="Permanent"])
summary(sub2$max[sub2$con=="Contract/Temporary"])
summary(sub2$max[sub2$con=="Contract/Temporary,Permanent"])
summary(sub2$max[sub2$con=="Unspecified"])

# Take **only** "Part Time" jobs.
sub<-sub2["Part Time"==sub2$hours,]

# Plot the salary min vs max.
ggplot(data=sub,aes(x=min,y=max,color=hours)) + 
       geom_point(size=2,alpha=0.25) + 
       labs(x="Salary Minimum",y="Salary Maximum")

# Look at the salaries produced - opens a new tab
page(sub2$sal)

# Take those jobs that only have "hour" in the salary
sub3<-sub[grepl("hour",sub$sal,ignore.case = TRUE),]

# Look at the salaries
length(sub3$sal)
page(sub3$sal)

# No longer need sub
rm(sub)

##########################################################
# Use regular expressions to identify non-annual salaries.
##########################################################

# Regular expression with a number of terms that can used to 
# identify hourly rates.
regexp <- paste(c("per hour",
                  "teaching hour",
                  "contact hour",
                  "contract hour",
                  "hourly",
                  "flat rate",
                  "an hour",
                  "per lecture",
                  "per session",
                  "per meeting",
                  "per delivery hour",
                  "per class hour",
                  "per day",
                  "per week",
                  "per month",
                  "hour course",
                  "single payment",
                  "monthly salary",
                  "per hr",
                  "/month",
                  "/week",
                  "fee",
                  "per term",
                  "direct teaching hour",
                  "/hr",
                  "living wage",
                  "monthly",
                  "termly",
                  "p/h",
                  "ph.",
                  "/term",
                  "/hour"),
                  sep="",collapse="|")

# How many cases does this regular expression capture?
p<-sub2[grepl(regexp,sub2$sal,ignore.case = TRUE),]
length(p$sal)
percent(length(p$sal)/n)
page(p$sal)

# No longer need this
rm(p)

# Compare to the number of max salaries under 10k
length(sub2$sal[sub2$max < 10000])
percent(length(sub2$sal[sub2$max < 10000])/n)

# Look at remaining salaries under 10k not captured by regexp
page(sub2$sal[sub2$max < 10000 & !(sub2$id %in% p$id)])

# Checking out if there are any other pertinent key words.
page(sub2$sal[grepl("stipend",sub2$sal,ignore.case = TRUE)])

# Filter out those jobs that match the keywords in the 
# regular expresion.
sub4<-sub2[grepl(regexp,sub2$sal,ignore.case = TRUE),]

# How many jobs have been picked up?
length(sub4$sal)

# Find out the composition of full/part time jobs
table(sub4$hours)

# Plot the salary min vs max with hours as the colouring 
# attribute...
ggplot(data=sub4,aes(x=min,y=max,color=hours)) + 
       geom_point(size=2,alpha=0.25)+ 
       labs(x="Salary Minimum",y="Salary Maximum")

# .. now use contracts as the attribute ...
ggplot(data=sub4,aes(x=min,y=max,color=con)) + 
  geom_point(size=2,alpha=0.25)+ 
  labs(x="Salary Minimum",y="Salary Maximum")

# Look at a histogram distribution of jobs
ggplot(data=sub4,aes(x=max,fill=hours)) + 
  geom_histogram(bins=10)+ geom_density() +
  xlim(0,10000) +
  labs(x="Maximum Salary",y="Number of Jobs")

ggplot(data=sub4,aes(x=max,fill=con)) + 
  geom_histogram(bins=10)+ geom_density() +
  xlim(0,10000) +
  labs(x="Maximum Salary",y="Number of Jobs")

# Look at the current job distribution
ggplot(data=sub2,aes(x=max,fill=hours)) + 
  geom_histogram(bins=10)+ geom_density() +
  xlim(0,10000) + ylim(0,1300) +
  labs(x="Maximum Salary",y="Number of Jobs")

# whole picture
ggplot(data=sub2,aes(x=max,fill=hours)) + 
  geom_histogram(bins=100)+ geom_density() +
  labs(x="Maximum Salary",y="Number of Jobs")

# Now take the converse of jobs that use the keywords.
sub5<- sub2[!(sub2$id %in% sub4$id),]

# How many jobs do we have?
cat(
"Number of original jobs ",length(dat$JobId),
", number of processed jobs ",length(sub2$id),
",\nthe number of jobs picked up by the regexp ",length(sub4$id),
"\nand the remaining jobs after use of the regexp ",length(sub5$id),".",
sep=""
)

# Look at the min-max distribution
ggplot(data=sub5,aes(x=min,y=max,color=hours)) + 
  geom_point(size=2,alpha=0.25)+ 
  labs(x="Salary Minimum",y="Salary Maximum")

# Histogram the jobs that have low salaries.
ggplot(data=sub5,aes(x=max,fill=hours)) + 
  geom_histogram(bins=10)+ geom_density() +
  xlim(0,10000) + ylim(0,1300) +
  labs(x="Maximum Salary",y="Number of Jobs")

############################################
# Look at ads for postgrad student positions
############################################

# Tabulate student positions - from the original data
m<-as.matrix(table(sub2$qualification))
m <- cbind(m,percent(m/n))
colnames(m)<-c("Number of Jobs", "Percent of Jobs")

pander(m,style="grid", 
       plain.ascii = TRUE,
       justify=c("left","right","right"),split.table=Inf)

# Look at the student positions where hourly salaries 
# have been removed
m<-as.matrix(table(sub5$qualification))
m <- cbind(m,percent(m/length(sub5$id)))
colnames(m)<-c("Number of Jobs", "Percent of Jobs")

pander(m,style="grid", 
       plain.ascii = TRUE,
       justify=c("left","right","right"),split.table=Inf)

###########################################
# Look at the postgraduate student salaries

# Create a copy of the original data
sub6 <- sub2

# Simplify the labelling for student posts
sub6$qualification[sub6$qualification != "Unspecified"]<-c("Postgrad")

# Quantify the number of jobs
m<-as.matrix(table(sub6$qualification))
m <- cbind(m,percent(m/length(sub6$id)))
colnames(m)<-c("Number of Jobs", "Percent of Jobs")

pander(m,style="grid", 
       plain.ascii = TRUE,
       justify=c("left","right","right"),split.table=Inf)

# Now just grab the jobs for student qualifications
sub6<-sub6[sub6$qualification == "Postgrad",]

# How many do we have?
length(sub6$id)

# See the salary spread
ggplot(data=sub6,aes(x=min,y=max,color=hours)) + 
  geom_point(size=2,alpha=0.25)+ 
  labs(x="Salary Minimum",y="Salary Maximum")

# Look at a summary of student data
length(sub6$id)
summary(sub6$max)

# UK only
length(sub6$id[sub6$uk == 1])
summary(sub6$max[sub6$uk == 1])

ggplot(data=sub6[sub6$uk == 1,],aes(x=min,y=max,color=hours)) + 
  geom_point(size=2,alpha=0.25)+ 
  labs(x="Salary Minimum",y="Salary Maximum")

# Remove the students jobs from the job list with the jobs
# that match the non-annual salary jobs.
sub5 <- sub5[!(sub5$id %in% sub6$id),]

# Plot the min-max distribution
# Look at the min-max distribution
ggplot(data=sub5,aes(x=min,y=max,color=hours)) + 
  geom_point(size=2,alpha=0.25)+ 
  labs(x="Salary Minimum",y="Salary Maximum")

# Look at the numbers for low salaries.
ggplot(data=sub5,aes(x=max,fill=hours)) + 
  geom_histogram(bins=10)+ geom_density() +
  xlim(0,10000) + ylim(0,1300) +
  labs(x="Maximum Salary",y="Number of Jobs")

# Look at the bigger picture
ggplot(data=sub5,aes(x=max,fill=hours)) + 
  geom_histogram(bins=100)+ geom_density() +
  labs(x="Maximum Salary",y="Number of Jobs")

# zoom in:
ggplot(data=sub5,aes(x=max,fill=hours)) + 
  geom_histogram(bins=10)+ geom_density() +
  xlim(0,10000) + ylim(0,75) +
  labs(x="Maximum Salary",y="Number of Jobs")

# Count the number of salaries < 10k
length(sub5$sal[sub5$max <10000])

# Get a summary for the max salaries
summary(sub5$max)

# Look at salaries less than £10k
page(sub5$sal[sub5$max <10000])

sub5$sal[sub5$max <5000]
