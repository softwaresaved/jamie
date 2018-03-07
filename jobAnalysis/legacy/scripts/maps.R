#!/usr/bin/env Rscript
#
# Taking the lead from:
#
# http://www.r-bloggers.com/r-beginners-plotting-locations-on-to-a-world-map/
# https://www.students.ncl.ac.uk/keith.newman/r/maps-in-r
#

library(ggmap)
library(maptools)
library(maps)
library(mapdata)
library(ggplot2)

# Set the working directory to be where this file is - you can
# add a line for your directory is and only execute that. Using
# the hostname to get a context based directory.
hostname<-Sys.info()["nodename"]

if(hostname == "mbp-ma.local"|hostname == "mbp-ma.lan"){
  setwd("/Users/mario/jobs-analysis/scripts")
}else{
  print("You need to set your current working directory.")
}

# Obtain auxilary functions.
source("R/filestuff.R")

# Read in the job data.
dat<-readJobsFile("../data/jobs.csv")

# Read in known locations
guk<-read.csv(file="../data/UKLocs.csv",
              stringsAsFactors = FALSE,
              strip.white = TRUE,
              col.names=c("name","lon","lat"))

# Remap some of the data (function in fileStuff.R)
dat<-cleanLocations(dat)

# Get the UK locations - split any comma separated values and give each
# their own entry. As a list can have a UK location and a non-UK location
# we need to clean these up. End up with a character array with all the known 
# UK lcations and some non-UK places.
uklocs<-unlist(strsplit(dat$Location[dat$InUK==1],","))

# Now grab identified software jobs
ukswlocs<-unlist(strsplit(dat$Location[dat$InUK==1 & dat$SoftwareJob==1],","))

# Need to remove spaces after splitting and collapsing the list.
uklocs <- sub("^\\s+", "", uklocs) # Trim leading spaces
uklocs <- sub("\\s+$", "", uklocs) # Trim trailing spaces

ukswlocs <- sub("^\\s+", "", ukswlocs) # Trim leading spaces
ukswlocs <- sub("\\s+$", "", ukswlocs) # Trim trailing spaces

# Produce a list of all the unique locations.
uknames<-levels(factor(uklocs))
ukswnames<-levels(factor(ukswlocs))

# List all locations not in the UK or ambiguous terms (e.g. Nationwide or 
# Northern Ireland which is in the UK but not a specific location). These
# slip through after unsplitting the list.
notinuk <- c("Aachen", "All Locations","Ankara","Antarctic","Australia",
             "Bangalore","Bangladesh","Bangon","Beijing","Bergen","Bideford","Boston",
             "Brazil",
             "China",
             "Dalian","Darmstadt","Durban",
             "Gaithersburg","Gambia","Geneva",
             "Havana","Hebei","Home","Hong Kong",
             "Kgs Lyngby","Kenya",
             "Leuven","Lyon",
             "Malaysia","Masai Mara","Melbourne","Molndal",
             "Nationwide", "Nairobi","Netherlands","Northern Ireland",
             "Paris","Perth",
             "Qatar",
             "Reduit","Rijswijk",
             "Santa Clara","Shanghai","Sierra Leone","Singapore","Switzerland","Sri Lanka",
             "Texas","Trento",
             "Uganda",
             "Virtual",
             "Wales","Wexford",
             "Xiamen",
             "Zurich"
)

# Remove locations not in the UK
uknames <- uknames[! uknames %in% notinuk]

ukswnames <- ukswnames[! ukswnames %in% notinuk]

# Remove duplicates
uknames <- levels(factor(uknames))

ukswnames <- levels(factor(ukswnames))

length(uknames)

length(ukswnames)

# Grab any new unknown locations
unknowns<-uknames[! uknames %in% guk$name]

# Count how many unknowns we have
length(unknowns)

if(length(unknowns)>0){
  
  # Query how many queries can be carried out. Can only do 2500
  # free queries per day.
  geocodeQueryCheck(userType="free")
  
  # Make the fact that we are using UK names explicit by appending
  # a ", UK" to every name when obtaining the lon & lat. Picking up
  # some aliases that are not in the UK. Of course, I am assuming 
  # that the British equivalent is meant mostly - could check the 
  # value in Location2.
  unknowns2<-gsub("(.*)","\\1, UK",unknowns)
  
  # This will create a data frame with the lon and lat of each location.
  # Appears to pull information from Google and has a restriction of a 
  # max of 2000 queries per day. Best to get the data and then to save
  # it. Next read from file and only query any unknown locations.
  guk2<-geocode(unknowns2) 
  
  # Aattach the place names to the data frame.
  guk2$name<- unknowns
  
  # Merge the data frame of knowns and unknowns
  guk<-rbind(guk,guk2[c("name","lon","lat")])
  
  # Save the data frame
  write.csv(guk[,c("name","lon","lat")],file="../data/UKLocs.csv",row.names = FALSE)
  
  # Remove variables we no longer need
  rm(unknowns2,guk2)
  
}

# Not using the following maps
#
#map.scale(160,-40,relwidth = 0.15, metric = TRUE, ratio = TRUE)
#
#map('worldHires', fill=TRUE, col="white", bg="lightblue",
#    c('UK', 'Ireland', 'Isle of Man','Isle of Wight', 'Wales:Anglesey'), 
#    xlim=c(-11,3), 
#    ylim=c(49,60.9))

# Now add the frequency of locations
ukfreq<-table(uklocs[uklocs %in% uknames])
tmp<-data.frame(name=names(ukfreq),num=as.numeric(ukfreq))
guk<-merge(guk,tmp,by="name")

ukswfreq<-table(ukswlocs[ukswlocs %in% ukswnames])
tmp<-data.frame(name=names(ukswfreq),num=as.numeric(ukswfreq))
guksw <- merge(guk,tmp,by="name")

# Get a UK map - not quite there yet
# Map types: terrain", "terrain-background", "satellite",
# "roadmap", "hybrid", "toner", "watercolor", "terrain=labels", "terrain-lines",
# "toner-2010", "toner-2011", "toner-background", "toner-hybrid",
# "toner-labels", "toner-lines", "toner-lite"

# This map looks ok but it shows chunks of europe
ukmap <- get_map(location = 'UK', 
                 zoom = 5,
                 maptype="watercolor",
                 source="stamen",
                 filename="ukmaptmp")

ukmap <- get_map(location = c(-9.23,49.84,2.69,60.85), #"UK", #c(lon = -0.1, lat = 51.5), 
                 zoom = "auto",
                 maptype="watercolor",
                 source="stamen",
                 filename="ukmaptmp")

# Bounding box for the UK - takes a while to generate. You
# can see the tiling of the map that is fetched.
ukmap <-get_stamenmap(bbox=c(-9.23,49.84,2.69,60.85),
                      maptype = "watercolor")

ukmap <-get_openstreetmap(bbox=c(-9.23,49.84,2.69,60.85),
                      maptype = "terrain")

# plot the points on a map
ggmap(ukmap, extent="panel") + 
      geom_point(data=guk,aes(x=lon,y=lat,size=num),col="red") +
      scale_size_area("Number of jobs",max_size=10)

ggmap(ukmap, extent="panel") + 
  geom_point(data=guksw,aes(x=lon,y=lat,size=num),col="blue") +
  scale_size_area("Number of software jobs",max_size=10)

#  + scale_size_area(max_size=10)
#  stat_density2d(data=guk,aes(x=guk$lon,y=guk$lat,size=guk$nums),col="red")
ukmap3<- ggmap(ukmap, 
               extent="panel") + 
  geom_point(data=guksw,aes(x=guksw$lon,y=guksw$lat,size=guksw$nums),col="blue")
ggmap(ukmap)
print(ukmap2)
print(ukmap3)
