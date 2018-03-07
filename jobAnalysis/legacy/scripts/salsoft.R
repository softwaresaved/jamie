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

# Map original data intos software and non software jobs
salary_soft <- dat$Salary[dat$SoftwareJob==1]   # Software job
salary_nsoft<- dat$Salary[dat$SoftwareJob==0]   # Non Software job
salmin_soft <- dat$SalaryMin[dat$SoftwareJob==1]
salmin_nsoft <- dat$SalaryMin[dat$SoftwareJob==0]
salmax_soft <- dat$SalaryMax[dat$SoftwareJob==1]
salmax_nsoft <- dat$SalaryMax[dat$SoftwareJob==0]

# Job ALA918, which has the £2,972,000 salary, is a non-software job.
# Remove.
salary_nsoft<-salary_nsoft[!grepl("£2,972,000",salary_nsoft)]
salmin_nsoft<-salmin_nsoft[!grepl("£2,972,000",salmin_nsoft)]
salmax_nsoft<-salmax_nsoft[!grepl("£2,972,000",salmax_nsoft)]

# Remove embedded spaces.
salmin_soft<-gsub(" ","",salmin_soft)
salmin_nsoft<-gsub(" ","",salmin_nsoft)

salmax_soft<-gsub(" ","",salmax_soft)
salmax_nsoft<-gsub(" ","",salmax_nsoft)

# Total number of jobs
n<-length(dat$Salary)
n1<-length(salmax_nsoft)
n2<-length(salmax_soft)
print(paste0("Total number of jobs: ",n," with ",n1,
             " non-software jobs ",n2," software jobs."))

# Count number of Unspecified
p1<-percent(length(salmin_nsoft[grepl("Unspecified",salmin_nsoft)])/n)
p2<-percent(length(salmin_soft[grepl("Unspecified",salmin_soft)])/n)
print(paste0("Percentage of unspecifed non-software jobs with salmin ",
             p1," and software jobs ",p2,"."))

p1<-percent(length(salmin_nsoft[grepl("Negotiable",salmin_nsoft)])/n)
p2<-percent(length(salmin_soft[grepl("Negotiable",salmin_soft)])/n)
print(paste0("Percentage of negotiable non-software salary jobs with salmin ",p1,
             " and software jobs ",p2,"."))

# Take entries that only specify a numerical salary.
uksalmin_nsoft<-salmin_nsoft[grepl("£",salmin_nsoft)]
uksalmin_soft<-salmin_soft[grepl("£",salmin_soft)]

uksalmax_nsoft<-salmax_nsoft[grepl("£",salmax_nsoft)]
uksalmax_soft<-salmax_soft[grepl("£",salmax_soft)]

# Strip out the commas and the pound sign
uksalmin_nsoft<-gsub("£|,","",uksalmin_nsoft)
uksalmin_soft<-gsub("£|,","",uksalmin_soft)

uksalmax_nsoft<-gsub("£|,","",uksalmax_nsoft)
uksalmax_soft<-gsub("£|,","",uksalmax_soft)

# Convert entries to numbers
u1<-as.numeric(uksalmin_nsoft)
u2<-as.numeric(uksalmin_soft)

summary(u1)
summary(u2)

hist(u2,xlim=c(0,80000),breaks=200,freq=FALSE,
     col=rgb(0,0,1,1/4), main="Min Non-Soft/Soft Salaries",
     xlab="Salary in £s"
)
hist(u1,xlim=c(0,80000),breaks=200,freq=FALSE,
     col=rgb(1,0,0,1/4), add=TRUE)
legend(60000,1e-04,c("non-Software","Software"),
       col=c(rgb(1,0,0,1/4),rgb(0,0,1,1/4)),pch=15,cex=0.75)

v1<-as.numeric(uksalmax_nsoft)
v2<-as.numeric(uksalmax_soft)

summary(v1)
summary(v2)

hist(v1,xlim=c(0,80000),ylim=c(0,2.3e-4),breaks=500,freq=FALSE,
     col=rgb(1,0,0,1/4), main="Max Non-Soft/Soft Salaries",
     xlab="Salary in £s"
)
hist(v2,xlim=c(0,80000),breaks=500,freq=FALSE,
     col=rgb(0,0,1,1/4), add=TRUE)
legend(60000,1e-04,c("non-Software","Softwarex"),
       col=c(rgb(1,0,0,1/4),rgb(0,0,1,1/4)),pch=15,cex=0.75)

