# Playing with the ggplot2 library.

# Librariese to load up
library(lattice)
library(ggplot2)
library(pander)
library(scales)

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

####################
# Look at contracts

con<-data.frame(contracts=dat$Contract)               # Create a new data frame
con$contracts<-gsub(" ","",con$contracts)             # Remove embedded spaces
con$contracts[con$contracts==""]<-c("Unspecified")    # Fill blanks with unspecified

# Do a quickplot of the data
qplot(contracts, 
      data=con, 
      fill=contracts, 
      geom="bar",
      ylab="Number of Jobs",
      xlab="Contract Type")

# Construct a table suitable for pander
mcon<-as.matrix(table(con$contracts))                  # Create a matrix
mcon<-cbind(mcon,percent(mcon/length(con$contracts)))  # Attach a column of %ages
colnames(mcon)<-c("Jobs with Contract Type","Percent") # Name the columns

# Plot in a form suitable for direct wiki input
pander(mcon,style="rmarkdown",justify=c("left","left","left"))

##################
# Look at salaries

# Create a new data frame with the data
sal<-data.frame(min=dat$SalaryMin,
                max=dat$SalaryMax,
                sw=dat$SoftwareJob,
                id=dat$JobId,
                role=dat$Role,
                stringsAsFactors = FALSE)

# Remove embedded spaces, pound symbols and commas/
sal$min<-gsub(" |£|,","",sal$min)
sal$max<-gsub(" |£|,","",sal$max)

# Remove any unspecified salaries (the - gives you the complement)
length(sal$min)                            # How many entries do we have?
grepl("Unspecified|Negotiable",sal)         # Do cols contain Unspecified or Negotiable?

# Remove rows that have unspsecified. Note the "-" and the ",".
sal<-sal[-grep("Unspecified|Negotiable",sal$min),]

# Recheck the lenght and whether cols contain Unspecified or Negotiable.
length(sal$min)
grepl("Unspecified|Negotiable",sal)

# Convert salaries to numbered columns.
sal$min<-as.numeric(sal$min)
sal$max<-as.numeric(sal$max)

# Check if we have any na values.
sum(is.na(sal$min))
sum(is.na(sal$max))

# Remove the line with the ~£3 job
sal<-sal[-grep("2972000",sal$min),]

# What are the max/min values?
max(sal$min)
max(sal$max)

# Fill any null entries with "Unspecified".
sal$role[sal$role==""]<-c("Unspecified")

# Substitute the entries for s/w and non s/w jobs.
sal$sw<-sub("0","non s/w job",sal$sw)
sal$sw<-sub("1","s/w job",sal$sw)

# Problem jobs where the min sal > max sal.
# "AJR068" "AKD035" "AJH720" "AKN455" "AJO448" "AJN930" "AJJ849" 
# "AKU597" "AJN951" "AKK389" "AJG538"
sal$id[sal$min>sal$max]

# Plot Max vs Min salaries and identify s/w jobs.
ggplot(data=sal, aes(x=min,y=max,colour=sw))+geom_point()+
  scale_x_continuous(limit=c(0,100000))+scale_y_continuous(limit=c(0,100000)) +
  labs(x="Salary Minimum",y="Salary Maximum")

# Plot Max vs Min Salaries and identify Roles (not a very meaningful plot)
ggplot(data=sal, aes(x=min,y=max,colour=role))+geom_point()+
  scale_x_continuous(limit=c(0,100000))+scale_y_continuous(limit=c(0,100000)) +
  labs(x="Salary Minimum",y="Salary Maximum")

# Above commands are more powerful
#
# qplot(min,
#       max,
#       data=sal,
#       xlab="Minum Salary",
#       ylab="Maximum Salary")  
# 
# qplot(SalaryMin,
#       SalaryMax,
#       data=dat,
#       colour=SoftwareJob)

# boxplot of the salaries:
boxplot(sal$min,sal$max,
        col=c("blue","red"),
        log="y",
        ylim=range(sal$max,na.rm=TRUE),
        ylab="Salary in Pounds",
        names=c("Salary Min","Salary Max"),pch=".")

# Look at subjects
#s<-data.frame()
#s$subject<-dat$Subject
#s$subject[s$subject==""]<-c("Unspecified")
sub<-dat$Subject
sub[sub==""]<-c("Unspecified")

# split string
sub<-unlist(strsplit(sub,";"))

# Another way of splitting 
# produces a data frame
# http://stackoverflow.com/questions/24595421/how-to-strsplit-data-frame-column-and-replicate-rows-accordingly
sub2<-data.frame(sub=dat$Subject,
                 min=dat$SalaryMin,
                 max=dat$SalaryMax,
                 stringsAsFactors = FALSE)

# Fill out any unspecifed elements explicitly
sub2$sub[sub2$sub == ""]<-c("Unspecified")

# Split the subject field on the semicolon
tmp<-strsplit(sub2$sub,";")

# Find the length of each sublist
len<-sapply(tmp,length)

# Bind as new rows and replicate existing ones
tmp<-cbind.data.frame(name=unlist(tmp), row=rep(1:nrow(sub2), times=len))

# Merge the rows between the sub2 and tmp data frames
sub2 <- merge(y=sub2, x=tmp, by.x="row", by.y="row.names", all.x=TRUE)[-1]

# Remove the original subject column
sub2<-sub2[,-c(2)]

# Process the salaries - remove pound sign and commas
sub2$min<-gsub(" |£|,","",sub2$min)
sub2$max<-gsub(" |£|,","",sub2$max)

# Need to remove rows based salaries
sub2<-sub2[-grep("Unspecified|Negotiable",sub2$min),]

# Convert salaries to numbers
sub2$min<-as.numeric(sub2$min)
sub2$max<-as.numeric(sub2$max)

# Single plot on one page (too many point types)
ggplot(data=sub2, aes(x=min,y=max,colour=name))+geom_point()+
  scale_x_continuous(limit=c(0,100000))+scale_y_continuous(limit=c(0,100000)) +
  labs(x="Salary Minimum",y="Salary Maximum")

# Multiple plots on one page (too small)
ggplot(data=sub2, aes(x=min,y=max,colour=name))+geom_point()+
  scale_x_continuous(limit=c(0,100000))+scale_y_continuous(limit=c(0,100000)) +
  labs(x="Salary Minimum",y="Salary Maximum")+facet_wrap(~name,ncol=1)+
  theme(legend.position="none") 

for( i in (levels(sub2$name))){
  n<-i                               # Create an output filename
  n<-gsub(",","",n)                  # Remove embedded commas
  n<-gsub(" ","_",n)                 # Replace spaces with underscores
  n<-paste0(n,".png")
  print(paste("Outputting data to",n))
  #png(filename=n)                    # Write the output to a png
  tmp<-sub2[grepl(i,sub2$name),]     # Extract the data
  ggplot(data=tmp, aes(x=min,y=max,colour=name))+geom_point()+
    scale_x_continuous(limit=c(0,100000))+scale_y_continuous(limit=c(0,100000)) +
    labs(x="Salary Minimum",y="Salary Maximum")+ggtitle(paste(i,"Salaries")) +
    theme(legend.position="none")
  ggsave(filename=n,plot=last_plot())
  i#dev.off()
}


# Plot salary densities by subject
for( i in (levels(sub2$name))){

  n<-i                               # Create an output filename
  n<-gsub(",","",n)                  # Remove embedded commas
  n<-gsub(" ","_",n)                 # Replace spaces with underscores
  n<-gsub("\\(","",n)                # Remove brackets
  n<-gsub("\\)","",n)                # Remove brackets
  n<-gsub("\\.","",n)                # Remove dots
  n<-paste0(n,"_den.png")
  tmp<-sub2[grepl(i,sub2$name),]     # Extract the data
  tmp<-tmp[,-c(1)]                   # Remove the name column
  if(length(tmp$min)==0|length(tmp$max)==0){ next}
  print(paste("Outputting data to",n))
  oo<-stack(tmp)
  ggplot(data=oo, aes(values,fill=ind))+geom_density(alpha=0.2)+
    scale_x_continuous(limit=c(0,100000))+
    labs(x="Salary",y="Density")+ggtitle(paste(i,"Salary Denisty")) 
  ggsave(filename=n,plot=last_plot())
}

#select(na.omit(concat.split.multiple(melt(df, id.vars="Column1"), 
#      split.col="value", sep=",", direction="long")), -time)

# Boxplot of all the salary spreads by subject. Problem is that 
# there are two many subjects.
ggplot(data=sub2,aes(x=name,y=min,fill=name)) +
   geom_boxplot() +
   scale_y_continuous(limit=c(0,100000)) +
   labs(x="Subject",y="Salary minimum in pounds") +
   theme(axis.text.x = element_text(angle=90, face="bold", colour="black",hjust=1.0)) +
   theme(legend.position="none") + coord_flip()
  
ggplot(data=sub2,aes(x=min,y=name,fill=name)) +
  geom_boxplot() +
  scale_x_continuous(limit=c(0,100000)) +
  labs(y="Subject",x="Salary minimum in pounds") +
  theme(legend.position="none")

#  + theme(axis.ticks = element_blank(), axis.text.x = element_blank())
#  + guides(col = guide_legend(nrow = 8))
#  + theme(legend.title = element_text(colour="blue", size=16, face="bold"))
#   scale_fill_manual(values=c(rainbow(length(levels(sub2$name)))), 
#                         name="Subjects",
#                         breaks=levels(sub2$name),
#                         labels=c(seq(1:length(levels(sub2$name)))))

# Remove unspecified tag else it swamps the data
s<-data.frame(sub=sub[! grepl("Unspecified",sub)])
qplot(sub,data=s,geom="bar")

# Tabulate the number of subjects
subtab<-as.matrix(table(sub2$name))
subtab<-cbind(subtab,percent(subtab/length(sub)))
colnames(subtab)<-c("Subjects","Percentage")
pander(subtab,style="rmarkdown",justify=c("left","left","left"),split.table=Inf)

#######
# Hours

hours<-dat$Hours
hours[hours==""]<-c("Unspecified")
mhours<-as.matrix(table(hours))
mhours<-cbind(mhours,percent(mhours/length(hours)))
colnames(mhours)<-c("Number of jobs","Percent")
pander(mhours,style="rmarkdown",justify=c("left","left","left"),split.table=Inf)

# Create an hours data frame
hdf<-data.frame(sub=dat$Subject,hrs=dat$Hours,stringsAsFactors=FALSE)

hdf$sub[hdf$sub==""] <- c("Unspecified")
hdf$hrs[hdf$hrs==""] <- c("Unspecified")

# Split the subject field on the semicolin
tmp<-strsplit(hdf$sub,";")

# Find the length of each sublist
len<-sapply(tmp,length)

# Bind the new rows and replicate
tmp<-cbind.data.frame(subj=unlist(tmp), row=rep(1:nrow(hdf), times=len))

# Merge the rows between sub2 and tmp
hdf <- merge(y=hdf, x=tmp, by.x="row", by.y="row.names", all.x=TRUE)[-1]

# Remove the original subject column
hdf<-hdf[,-c(2)]

# Tabulate this inforation
mhdf<-as.matrix(table(hdf))
pander(mhdf,style="rmarkdown",justify=c("left","left","left","left","left"),
       split.table=Inf)

##############
# Broken stuff

# Barplot of the distribution
ggplot(barchart) + geom_bar(data=sub2,aes(x=min),fill="blue",alpha=0.2) + 
  geom_bar(data=sub2,aes(x=max),fill="red",alpha=0.2) + 
  scale_x_continuous(limit=c(0,100000))

ggplot(data=sub2,aes(x=min,fill="red",alpha=0.2),binwidth=1000) + 
  geom_bar(data=sub2,aes(x=max,fill="blue",alpha=0.2),binwidth=1000) + 
  scale_x_continuous(limit=c(0,100000))

# Try a histogram
ggplot(data=sub2,mapping=aes(x=min,fill=name)) + 
  geom_histogram(binwidth=2000,alpha=0.2,position="identity") + 
  scale_x_continuous(limit=c(0,100000))

ggplot(data=sub2,mapping=aes(x=min,fill=name)) + 
  geom_density(alpha=0.2) + 
  scale_x_continuous(limit=c(0,100000))
