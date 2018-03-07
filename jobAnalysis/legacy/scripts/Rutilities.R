# Routines to load up the jobs.csv data into R. Best to copy-paste
# the specific routines into the R window.
# Best way of doing this is to install R studio (you will also need
# R on your machine):
#
#     http://www.rstudio.com/
#
# Then at the end of everyline you want to execute you type 
# Cnt-Return and that command will be executed.
#
# If you need to get help on any routine type help(routineName) 
# or ?routineName in the console window and some help should 
# come out or you can use ??routineName to do a search for that 
# routine.

# Useful R commands:
#
# methods(libraryname) - gives you a list of the available methods
#                        can also run on functions - shows you the aliases.
#
# getAnywhere(name)   - searches for objects with the the name. Returns the 
#                       corresponding object.
#
# Sys.info() - overview of the system.
#
# Other useful R utilities sample, subset.

#library(microbenchmark)
library(lattice)
library(ggplot2)
library(pander)

# Good references:
#
# R Cookbook: http://www.cookbook-r.com/
#

###################
# Load the data in.

# Set the working directory to be where the file is - you can
# add a line for your directory is and only execute that.
hostname<-Sys.info()["nodename"]

if(hostname == "mbp-ma.local"){
  setwd("/Users/mario/jobs-analysis/scripts")
}else{
  print("You need to set your current working directory.")
}

# Obtain functions to read data.
source("R/filestuff.R")

# Read in the data.
dat<-readJobsFile("../data/jobs.csv")

# Can check the names of variables in the data frame.
names(dat)

# Let's generate a frequency plot
summary(dat$SalaryMin) # A summary of the minimum salary

# Plot a histogram
hist(table(dat$SalaryMin), 
     main="Minimum Salary Distribution", 
     col="red", xlab="Salary", ylab="Frequency")

hist(table(dat$SalaryMax), 
     main="Maximum Salary Distribution", 
     col="green", xlab="Salary", ylab="Frequency")

# Use barcharts

barchart(table(dat$SalaryMin), 
         main="Minimum Salary Distribution", 
         col="red", xlab="Salary", ylab="Frequency")

# Locations in the uk
ukloc<-dat$Location[dat$InUK==1]

# Russell group of Universities
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

# Jobs in the UK russell group
rg <- factor(dat$Employer[dat$Employer %in% russell]) # Grab Russell group
ukrus <- factor(gsub("-"," ",rg))                     # Replace "-" with spaces

# Rename "london school of economics and political science" to "lse"
ukrus<-gsub("london school of economics and political science","lse",ukrus)

par(mai=c(2.5,1,1,1)) # Change the margins to fit the xlabels

barplot(table(ukrus),col=rainbow(24),las=2,
        ylab="Numbers",
        main="Jobs within Russell Group",
        cex.names = 0.7)

par(mai=c(1,1,1,1)) # return the margins to the original size

# Identify only the softare jobs in the Russell group
ukrussoft<-dat$Employer[(dat$SoftwareJob==1)]
ukrussoft<-ukrussoft[ukrussoft %in% russell]
ukrussoft<-factor(gsub("-"," ",ukrussoft))

# Rename "london school of economics and political science" to "lse"
ukrussoft<-gsub("london school of economics and political science","lse",ukrussoft)

par(mai=c(2.5,1,1,1)) # Change the margins to fit the xlabels 

barplot(table(ukrussoft),col=rainbow(24),
        las=2,
        cex.names = 0.7,
        ylab="Numbers",
        main="Software jobs in Russell Group")

par(mai=c(1,1,1,1)) # return the margins to their original setting

# Work out the percentage of Russel group jobs
rgswpc<-round(table(ukrussoft)/table(ukrus)*100,2)
par(mai=c(2.5,1,1,1)) # Change the margins to fit the xlabels 
barplot(rgswpc,col=rainbow(24),
        las=2,
        cex.names = 0.7,
        ylab="Percent",
        main="Percentage software jobs in Russell Group")
par(mai=c(1,1,1,1)) # return the margins to their original setting

# Combine the separate columns into one array
tb<-cbind(table(ukrussoft),table(ukrus),rgswpc)
colnames(tb)<-c("RG Software Jobs","RG Jobs","% Software Jobs")
pander(as.matrix(tb),style="rmarkdown",
       justify=c("left","left","left","left"),split.table=Inf)

# Print a busy pie chart
pie(summary(ukloc))

# library(ggplot2)

# Useful commands
#
# struct(var) str(var)
# length(var)
# class(var)
# levels(var)

# Get dates job opening dates
d1 <- as.Date(dat$PlacedOn,"%d/%m/%Y")

# Plot the number of jobs number of job openings by date
hist(d1,"weeks",format="%F", freq = TRUE, 
     col=rainbow(52),
     xlab="Date", 
     ylab="Number of Jobs",
     main="Job downloads per week")

# Get the job closing dates.
d2 <- as.Date(dat$Closes,"%d/%m/%Y")

# Calculate the number of days the job is open.
d3 <- as.numeric(na.omit(d2-d1))

# Plot the number of days the job is open - not sure I believe this graph.
# Have plotted in excel before and got peaks at 2 weeks and one month. This
# just seems to be a monotonic drop.
barplot(summary(factor(d3)),ylab="Number of Jobs",xlab="Days from open to close")

# This one is more believable
hist(d3,breaks=2000,xlim=c(0,100),freq=TRUE,xlab ="Days between job is open",ylab="Number of Jobs",col="red",main="Days a job is available for")

# Generate a cumulative sum of the jobs downloaded
tab1<-table(d1)
tab2<-cumsum(tab1)
barplot(tab2,
        col="cyan",
        xlab="Dates",
        ylab="Total Number of Jobs Downloaded")

# Process the subject information
# Get information about the subjects
a<-as.character(dat$Subject)  # Get the subject information
a[a==""]="unspecified"        # Fill in null entries with unspecified
a<-unlist(strsplit(a,";"))    # Split the entries with semicolons

# Tabulate computer languates
# Other languages that should be there but will probably give a lot of false
# positives: C, R
# Add as languages? jquery, html

langs <- c(
           "asp.net",
           "c++",   #"c\\+\\+",
           "c#",
           "fortran",
           "genstat",
           "hadoop",
           "haskell",
           "java",
           "javascript",
           "julia",
           "matlab",
           "nosql",
           "pascal",
           "perl",
           "php",
           "python",
           "ruby",
           "sas",
           "scala",
           "spark",
           "spss"
           )

cl <- data.frame(lan=character(),n=numeric(),stringsAsFactors = FALSE)

for(l in langs){ 
  n<-length(grep(paste0("(\b|[:[punct:]?)",l,"(\b|[:[punct:]?|[0-9]+)"),
          dat$Description, value = FALSE, ignore.case=TRUE))
  l<-gsub("\\","",l,fixed=TRUE)   # Remove backslashes
  cl[nrow(cl)+1,]<-c(l,n)
  print(paste("Language ",l," has ", n," jobs."))
}

# Playing with the location array
length(dat$Location)            # Raw data
length(table(dat$Location))     # Frequency table length
# Locations may have comma separated values split these
locs<-unlist(strsplit(dat$Location,",")) # split csv into individual entries
length(table(locs))                      # count the frequency table

# This will turn up false positives because a list of comma separated
# locations is in the UK if one of those entries is in the UK.
uklocs<-unlist(strsplit(dat$Location[dat$InUK==1],","))
length(table(uklocs))
barplot(table(uklocs)[table(uklocs)>100],las=2,cex.axis=1.0,cex.names=0.5,col="red")


# Get dates jobs 
d1 <-as.Date(dat$PlacedOn,"%d/%m/%Y")

# Plot the number of jobs downloaded
hist(d1,"weeks",format="%F", freq = TRUE, 
     col=rainbow(52),
     xlab="Date", 
     ylab="Number of Jobs",
     main="Job downloads")

barplot(table(d1),col="red", xlab="Date", 
        ylab="Number of Jobs",
        main="Job downloads")

d2 <-as.Date(dat$PlacedOn[dat$SoftwareJob == 1],"%d/%m/%Y")
d3 <-as.Date(dat$PlacedOn[! dat$SoftwareJob == 1],"%d/%m/%Y")

barplot(table(d2),col="blue", xlab="Date", 
        ylab="Number of Software Jobs",
        main="Software Job downloads")
ggplot(sw)
ggplot() +
  geom_point(data = nsw) +
  geom_point(data = sw, colour = "red")

# Find frequency of terms
freqs <- as.data.frame(inspect(dtm))
f<-colSums(freqs)
f["fotran"]

# Mention of computer languages
l <- f[langs] 
l <- l[!is.na(l)]
barchart(l,
         xlab="Number of Mentions",
         ylab="Computer language",
         col="red")

# Find out which Universities have the most IT jobs
# grepl returns a logical if the term is found - so get
# UK jobs that are also classed as IT jobs.
a<-dat$Employer[dat$InUK == 1 & grepl("IT",dat$Subject)]

# Map hyphens to spaces.
a<-gsub("-"," ",a)

# Get a frequency table.
a<-table(a)

# Sort the data.
a<-sort(a,decreasing = TRUE) 

# Only show employers with more than 15 entries.
a<-a[a > 15]

# Plot the result.
barchart(a,
         xlab="Number of IT Jobs",
         col="red")

# Look at the distribution
hist(a,breaks=c(70),xlab="Number of Jobs",ylab="Number of institutions",col="red",main="")

# Count the number of occurrences of different computing languages.
# This is probably not the best way to do it.
m <- list()
for(l in langs){
  if(l == "c++") l<-"c\\+\\+"
  n<-sum(grepl(l,dat$Description,ignore.case = TRUE))
  m[[l]]<-n
}
u<-unlist(m)
names(u)<-gsub("\\\\","",names(u))
barchart(u,col="red",xlab="Jobs mentoning")
u<-as.matrix(u)
colnames(u)<-c("Jobs Mentioning")
pander(u,style="rmarkdown",justify=c("left","left"))

# Construct a reg expression for words currently used to identify s/w jobs.
sfw_words<-paste("software developer",
                   "coding",
                   "coder",
                   "research software engineer",
                   "software engineer",
                   "programming",
                   "programme",
                   "Fortran",
                   "C\\+\\+",
                   "Java",
                   "JavaScript",
                   "MATLAB",
                   "Python",
                   "Perl",
                   sep="|")

# Check that we get the same result as our classifier
jobs<-paste(dat$Name,dat$Description) 
sum(grepl(sfw_words,jobs,ignore.case = TRUE)) # 23731/60068

# Number of jobs
table(dat$SoftwareJob,useNA="ifany")

# Print job ids that are not defined as software/non-software jobs.
dat$JobId[is.na(dat$SoftwareJob)]

# Number of jobs where the software term is in the job name
length(grep("T|TB",dat$SoftTermIn)) # 497/60068

# Using the same terms how many can we identify in the job name.
length(grep(sfw_words,dat$Name,ignore.case = TRUE)) # 1784/60068 - Not consistent

# Number of jobs where the software term is in the job body
length(grep("B|TB",dat$SoftTermIn)) # 4191/60068 

# Using the same terms how many can we identify in the job name.
length(grep(sfw_words,dat$Description, ignore.case = TRUE)) # 23612/60068 - Not consistent

# Checking the classification consistency between software jobs and the IT and 
# computer science jobs as identified in the Subject.
length(dat$JobId)
length(dat$JobId[dat$SoftwareJob==1])
length(dat$JobId[grepl("IT",dat$Subject)])
length(dat$JobId[grepl("IT",dat$Subject)&dat$SoftwareJob==1])
length(dat$JobId[grepl("IT",dat$Subject)&dat$SoftwareJob==0])
length(dat$JobId[grepl("Computer Science",dat$Subject)])
length(dat$JobId[grepl("Computer Science",dat$Subject)&dat$SoftwareJob==1])
length(dat$JobId[grepl("Computer Science",dat$Subject)&dat$SoftwareJob==0])

