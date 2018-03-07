# Use R to try and look at the salary information in the jobs file

# Load up any libraries needed
library(lattice)
library(scales)
library(ggplot2)

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

# Check for problem entries:
# 352
# 190
# 0
u<-dat$JobId[!grepl("£|€|Unspecified|Negotiable",dat$SalaryMin)|
               !grepl("£|€|Unspecified|Negotiable",dat$SalaryMax)]
n<-length(u)
print(paste0("Number of possible problem jobs ",n,"."))
u # List the entries if not too many.

# Map original data
salary <- dat$Salary
salmin <- dat$SalaryMin
salmax <- dat$SalaryMax

# Job ALA918 offers £2,972,000 monthly (no taxation for 2 years for UK citizens)
# That simply cannot be right and is skewing the results so removing.
salary<-salary[!grepl("£2,972,000",salary)]
salmin<-salmin[!grepl("£2,972,000",salmin)]
salmax<-salmax[!grepl("£2,972,000",salmax)]

# Remove embedded spaces.
salmin<-gsub(" ","",salmin)
salmax<-gsub(" ","",salmax)

# Total number of jobs
n<-length(salary)
print(paste0("Total number of jobs: ",n,"."))

# Count number of Unspecified salaries
p1<-percent(length(salmin[grepl("Unspecified",salmin)])/n)
p2<-percent(length(salmax[grepl("Unspecified",salmax)])/n)
print(paste0("Percentage of unspecifed salary jobs with salmin ",p1," and salmax ",p2,"."))

# Count the number of Negotiable salaries
p1<-percent(length(salmin[grepl("Negotiable",salmin)])/n)
p2<-percent(length(salmax[grepl("Negotiable",salmax)])/n)
print(paste0("Percentage of negotiable salary jobs with salmin ",p1," and salmax ",p2,"."))

# Take entries that only specify a numerical salary.
uksalmin<-salmin[grepl("£",salmin)]
uksalmax<-salmax[grepl("£",salmax)]
p1<-percent(length(uksalmin)/n)
p2<-percent(length(uksalmax)/n)
print(paste0("Using ",p1," of the salmin entries and ",p2," of the salmax entries."))

# Strip out the commas and the pound sign
uksalmin<-gsub("£|,","",uksalmin)
uksalmax<-gsub("£|,","",uksalmax)

# Convert entries to numbers
u<-as.numeric(uksalmin)
v<-as.numeric(uksalmax)

# Print out problematical entries
u1<-uksalmin[is.na(u)]
n1<-length(u1)
print(paste("uksamin has a problen with the following",n1,"entries: "))
u1
u2<-uksalmax[is.na(v)]
n2<-length(u2)
print(paste("uksalmax has a problen with the following",n2,"entries: "))
u2

# Summary and boxplot of the min salary
summary(u)
boxplot(u,xlab="Min Salary Spread in £s",horizontal = TRUE)
barchart(table(u))
hist(u,xlim=c(0,80000),breaks=1000,
     col="red",
     xlab="Salary in £s",
     main="Minimum Salary Distribution")

# Summary and boxplot of the max salary
summary(v)
boxplot(v,xlab="Max Salary Spread in £s",col="red",log="y",horizontal = TRUE)
hist(v,xlim=c(0,80000),breaks=1000,
     col="blue",
     xlab="Salary in £s",
     main="Maximum Salary Distribution")

# Resources:
#
#  http://www.cookbook-r.com/Graphs/
#

# Plot the two distributions side by side
# Plots appear to be on top of each other
hist(u,xlim=c(0,80000),breaks=750,
     col=rgb(1,0,0,1/4), main="Distribution of Salaries",
     xlab="Salary in £s")
hist(v,xlim=c(0,80000),breaks=750,
     col=rgb(0,0,1,1/4), 
     add=TRUE)
legend(65000,8000,c("Salary Min","Salary Max"),
       col=c(rgb(1,0,0,1/4),rgb(0,0,1,1/4)),pch=15,cex=0.75)
