#!/usr/bin/env Rscript
#
# R script to create a summary of the jobs data. The script reads
# in the data from the jobs.csv file and processes this writing the
# output to a summary/index.html file. 
#

# Load libraries that are required
library(lattice)
library(xtable)

#######################
# Reading in the data #
#######################

source("R/filestuff.R")

dat<-readJobsFile(file="../data/jobs.csv")

############################
# Creating auxilary arrays #
############################

# Define the Russell group of Universities
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

##################################################
# Processing data and writing out a summary file #
##################################################

# Root directory of where files will go
rootdir="summary"

# Subdirectory where the images are to be found
imgs = "imgs"

# Subdirectory which images will be written to
imgdir=paste0(rootdir,"/",imgs)

# Create the output subdirectories if these do not already exist.
dir.create(file.path(paste0(imgdir)),
           recursive=TRUE,
           showWarnings = FALSE)

# Redirect output to an external file
sink(paste0(rootdir,"/","index.html"))

#######################
# Write an html header

cat("<html>
<head>
<title>
")
cat(paste("Summary result generated on: ",Sys.time()))
cat("
</title>
</head>
<body>
<h1>
Job Downloads Summary Results
</h1>
<h2>Contents</h2>
<ul>
<li><a href=\"#summary\">Summary</a></li>
<li><a href=\"#location\">Location</a></li>
<li><a href=\"#misc\">Misc</a></li>
</ul>
<h2 id=\"summary\">Summary</h2>
")

############################
# Summary of results section

cat("<table>\n")
cat(paste("<tr><td>Total number of jobs downloaded: </td><td>",
    length(dat$JobId),"</td></tr>\n"))
cat(paste("<tr><td>Total number of jobs in the UK: </td><td>",
    sum(as.numeric(dat$InUK),na.rm=TRUE),"</td></tr>\n"))
cat(paste("<tr><td>Total Possible software jobs: </td><td>",
    sum(as.numeric(dat$SoftwareJob)),"</td></tr>\n"))
cat(paste("<tr><td>Total Possible software jobs in UK: </td><td>",
    sum(as.numeric(dat$SoftwareJob&dat$InUK)) ,"</td></tr>\n"))
cat("</table>\n")

cat("<p>\nNumber of jobs downloaded per week:\n</p>\n")

outfile <- "job-freq.html"

png(paste0(imgdir,"/",outfile))

# Get dates jobs 
d1 <-as.Date(dat$PlacedOn,"%d/%m/%Y")

# Plot the number of jobs downloaded
hist(d1,"weeks",format="%F", freq = TRUE, 
     col=rainbow(52),
     xlab="Date", 
     ylab="Number of Jobs",
     main="Job downloads per week")

cat(paste0("<img src=\"",imgs,"/",outfile,"\" "))
cat(paste("alt=\"Job download frequency\"/>\n"))

# Number of days a job is available for

cat("<p>\nNumber of days a job is available for:\n</p>\n")

outfile <- "job-days-freq.html"

png(paste0(imgdir,"/",outfile))

# Get the job closing dates.
d2 <- as.Date(dat$Closes,"%d/%m/%Y")

# Calculate the number of days the job is open.
d3 <- as.numeric(na.omit(d2-d1))

hist(d3,
     breaks=2000,
     xlim=c(0,100),
     freq=TRUE,
     xlab ="Days between job is open",
     ylab="Number of Jobs",
     col="red",
     main="Days a job is available for")

cat(paste0("<img src=\"",imgs,"/",outfile,"\" "))
cat(paste("alt=\"Number of days a job is available for\"/>\n"))

# Cumulative number of jobs downloaded

cat("<p>\ncumulative number of jobs downloaded:\n</p>\n")

outfile <- "cumulative-job-days-downloaded.html"
png(paste0(imgdir,"/",outfile))

tab1<-table(d1)
tab2<-cumsum(tab1)
barplot(tab2,
        col="cyan",
        xlab="Dates",
        ylab="Total Number of Jobs Downloaded")

cat(paste0("<img src=\"",imgs,"/",outfile,"\" "))
cat(paste("alt=\"Cumulative number of jobs downloaded\"/>\n"))

rm(tab1,tab2)

##################
# Location section

# Check out:
# http://stackoverflow.com/questions/16227223/aggregate-by-factor-levels-keeping-other-variables-in-the-resulting-data-frame
# for aggregating data and not just truncating it.

# New section header
cat("<h2 id=\"location\">Location</h2>\n")


# Point at which to truncate values.
valgreater=750

cat(paste("<p>\nShowing locations with values greater than ",valgreater,
"jobs (for now ignoring values less than ",valgreater," (will fix this to",
" do proper aggregation once I know how).\n</p>\n"))

# Image file to write to
outfile="loc-pie.png"

# Need to use paste0 so it does not embed spaces when joining
png(paste0(imgdir,"/",outfile))

pie(table(dat$Location)[as.numeric(table(dat$Location))>valgreater],
            col=rainbow(24))

cat(paste0("<img src=\"",imgs,"/",outfile,
           "\" alt=\"Location pie chart\"/>\n"))

cat("<p>\nSame information as a bar chart:\n</p>\n")

outfile="loc-bar.png"
png(filename=paste0(imgdir,"/",outfile))

barchart(table(dat$Location)[as.numeric(table(dat$Location))>valgreater],
         xlab="Number of Jobs",col=rainbow(24))

cat(paste0("<img src=\"",imgs,"/",outfile,"\" "))
cat(paste("alt=\"Locations bar chart\"/>\n"))

cat("<p>\nUsing Location informtion which is a bit more coarse grained:\n</p>\n")

outfile="loc2-bar.png"
png(filename=paste0(imgdir,"/",outfile))

barchart(table(dat$Location2),
         freq = TRUE,col=rainbow(24)
         ,xlab="Numbers",
         ylab="Locations")

cat(paste0("<img src=\"",imgs,"/",outfile,"\" "))
cat(paste("alt=\"Locations bar chart\"/>\n"))

# Print a table with the actual numbers
t<-as.matrix(summary(dat$Location2))
colnames(t)<-c("Number of Jobs")
print(xtable(t), type="html")

# Get information about the subjects
cat("<p>\nNumber of jobs for classifications:\n</p>\n")

a<-as.character(dat$Subject)  # Get the subject information
a[a==""]="Unspecified"        # Fill in null entries with unspecified
a<-unlist(strsplit(a,";"))    # Split the entries with semicolons
a<-table(a)
print(xtable(a),type="html",include.colnames = FALSE)
rm(a)

########################
# Russell Group section

# Put in a new section header
cat("<h2 id=\"misc\">Misc</h2>\n")

cat("<p>\nEmployer universities in the Russell group\n</p>\n")

# What to call the output file
outfile<-"russell-bar.png"

# Write the graph to this file
png(filename=paste0(imgdir,"/",outfile))

# Identify employers in the russell group and  substitute "-" with " "s
ukrus <- factor(gsub("-"," ",dat$Employer[dat$Employer %in% russell]))

# Print out html to display the resulting graph
cat(paste0("<img src=\"",imgs,"/",outfile,
           "\" alt=\"Russell group bar chart\"/>\n"))

# Generate the graph
old<-par("mai")
par(mai=c(2.5,1,1,1)) # Change the margins to fit the xlabels
a<-ukrus
a<-gsub("london school of economics and political science","LSE",a)
barplot(table(a),col=rainbow(24),las=2,ylab="Numbers",cex.names=0.7,
        main="Jobs within Russell Group")

# Reinstate the old margins
par(mai=old)

# Now do the same thing for software jobs.

cat("<p>
Software jobs only from employers in the Russell group of Universities:
</p>")

# What to call the output file
outfile="russell-sw-bar.png"

# Write the graph to this file
png(filename=paste0(imgdir,"/",outfile))

# Reset the margins
old<-par("mai")
par(mai=c(2.5,1,1,1)) # Change the margins to fit the xlabels

# Select the software jobs first
u<-factor(dat$Employer[(dat$SoftwareJob==1)])

# Now take select the employers in the Russell group
u<-factor(gsub("-"," ",u[u %in% russell]))

# Shorten the LSE name.
u<-gsub("london school of economics and political science","LSE",u)

# Generate the graph
barplot(table(u),col=rainbow(24),las=2,ylab="Numbers",cex.names=0.7,
        main="Software jobs in Russell Group")

# Reinstate the old margins
par(mai=old)

# Print out html to display the resulting graph
cat(paste0("<img src=\"",imgs,"/",outfile,"\" "))
cat(paste("alt=\"Russell group software bar chart\"/>\n"))


####################
# Add an html footer
cat(paste(
"<p/>\n<hr/>\n",
"<div align=\"right\">\n<small><i>Result generated on: ",date(),
"</i></small>\n</div>"))

# Write the html close
cat("
</body>
</html>
")

# Finish redirecting output
sink()
