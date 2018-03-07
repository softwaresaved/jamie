# File stuff: functions for reading and cleaning data.
#

readTrainingFile<-function(fileName)
{

  # Column names
  cn = c("jobid","user","class")

  # Read the file
  dat<-read.csv(file=fileName,
                stringsAsFactors = FALSE,
                strip.white = TRUE,
                sep=",",
                col.names=cn)
  
  # Return the 
  return(dat)

}

readJobsFile<-function(fileName)
{
  
  # Column names
  cn = c("JobId",
         "Name",
         "Employer",
         "Location",
         "InUK",
         "SoftwareJob",
         "SoftTermIn",
         "Salary",
         "SalaryMin",
         "SalaryMax",
         "Hours",
         "Contract",
         "FundingFor",
         "QualifcationType",
         "PlacedOn",
         "Closes",
         "JobRef",
         "h1",
         "h2",
         "h3",
         "Role",
         "Subject",
         "Location2",
         "Description")
  
  # Read the contents into a data frame
  # Now read the data into dat (a data frame)
  # Useful crib sheet: https://www.zoology.ubc.ca/~schluter/R/data/
  dat<-read.csv(file=fileName,
                encoding="UTF-8",
                stringsAsFactors = FALSE,
                strip.white = TRUE,
                sep=",",
                col.names=cn)
  
  # Clean up salaries mins and maxes that have not been parsed
  # correctly.
  dat<-cleanSalaries(dat)
  
  # Replace dashes with spaces for the employer
  dat$Employer <- gsub("-"," ",dat$Employer)
  
  # Convert dates into date types
  dat$PlacedOn <- as.Date(dat$PlacedOn,"%d/%m/%Y")
  dat$Closes   <- as.Date(dat$Closes,"%d/%m/%Y")
  
  # Initialise data that does not currently have any values.
  dat$Subject[dat$Subject == ""]                   <- c("Unspecified")
  dat$Contract[dat$Contract == ""]                 <- c("Unspecified")
  dat$QualifcationType[dat$QualifcationType == ""] <- c("Unspecified")
  dat$FundingFor[dat$FundingFor == ""]             <- c("Unspecified")
  dat$Hours[dat$Hours == ""]                       <- c("Unspecified")
  
  # Kill spaces for contracts
  dat$Contract <- gsub(" ","",dat$Contract)
  
  # Return the 
  return(dat)
}

# Clean data - remap data Locations
cleanLocations <- function(dat)
{
  # Trim leading and trailing spaces from the Locations
  dat$Location <- sub("^\\s+", "", dat$Location) # Trim leading spaces
  dat$Location <- sub("\\s+$", "", dat$Location) # Trim trailing spaces
  
  # Remap postcodes to actual locations
  dat$Location <- sub("Cf10 2", "Cardiff", dat$Location)
  dat$Location <- sub("Cf24 0", "Cardiff", dat$Location)
  dat$Location <- sub("Cf24 2", "Cardiff", dat$Location)
  dat$Location <- sub("Cf37 1", "Cardiff", dat$Location)
  dat$Location <- sub("Cf37 4", "Cardiff", dat$Location)
  dat$Location <- sub("E1 4", "London", dat$Location)
  dat$Location <- sub("Ec1y 8", "London", dat$Location)
  dat$Location <- sub("Np12 1", "Caerphilly", dat$Location) 
  dat$Location <- sub("Pr1 2", "Preston", dat$Location)
  dat$Location <- sub("se1 8", "London", dat$Location)
  dat$Location <- sub("Se1 8", "London", dat$Location)
  dat$Location <- sub("Tw20 0", "London", dat$Location)
  dat$Location <- sub("Ub8 3", "London", dat$Location)
  dat$Location <- sub("Wc1e 7", "London", dat$Location)
  dat$Location <- sub("Wc1h 0", "London", dat$Location)
  dat$Location <- sub("Wc1v 7", "London", dat$Location)
  dat$Location <- sub("Wc1x 0", "London", dat$Location)
  dat$Location <- sub("Wc2r 0", "London", dat$Location)
  
  # Remap districts
  dat$Location <- sub("Acton", "London", dat$Location)
  dat$Location <- sub("Bromley", "London", dat$Location)
  dat$Location <- sub("Camden", "London", dat$Location)
  dat$Location <- sub("Chelsea", "London", dat$Location)
  dat$Location <- sub("City Of Westminster", "London", dat$Location)
  dat$Location <- sub("City Of London", "London", dat$Location)
  dat$Location <- sub("Covent Garden", "London", dat$Location)
  dat$Location <- sub("Croydon", "London", dat$Location)
  dat$Location <- sub("Ealing", "London", dat$Location)
  dat$Location <- sub("Euston", "London", dat$Location)
  dat$Location <- sub("Finchley", "London", dat$Location)
  dat$Location <- sub("Hammersmith", "London", dat$Location)
  dat$Location <- sub("Holborn", "London", dat$Location)
  dat$Location <- sub("London Town", "London", dat$Location)
  dat$Location <- sub("Miles End", "London", dat$Location)
  dat$Location <- sub("Morningside", "Edinburgh", dat$Location)
  dat$Location <- sub("Np20 2", "Newport", dat$Location)
  dat$Location <- sub("Paddington", "London", dat$Location)
  dat$Location <- sub("Richmond Upon Thames", "London", dat$Location)
  dat$Location <- sub("Shepherds Bush", "London", dat$Location)
  dat$Location <- sub("Southwark", "London", dat$Location)
  dat$Location <- sub("South Kensington", "London", dat$Location)
  dat$Location <- sub("Tottenham", "London", dat$Location)
  dat$Location <- sub("Twickenham", "London", dat$Location)
  dat$Location <- sub("Waterloo", "London", dat$Location)
  dat$Location <- sub("Wimbeldon", "London", dat$Location)
  dat$Location <- sub("Whitechapel", "London", dat$Location)

  # Other degeneracies
  dat$Location <- sub("Egham, Tw20 0", "Egham", dat$Location)
  dat$Location <- sub("Henley On Thames", "Henley", dat$Location)
  dat$Location <- sub("Londonderry County Borough", "Londonderry", dat$Location)
  dat$Location <- sub("Leamington Spa", "Leamington", dat$Location)
  dat$Location <- sub("Middlesbrough", "Middlesborough", dat$Location)
  dat$Location <- sub("Newcastle-on-tyne", "Newcastle", dat$Location)
  dat$Location <- sub("Newcastle Upon Tyne", "Newcastle", dat$Location)
  dat$Location <- sub("Southend-on-sea", "Southend", dat$Location)
  dat$Location <- sub("Stoke-on-trent", "Stoke", dat$Location)
  dat$Location <- sub("Stoke-upon-trent", "Stoke", dat$Location)
  
  # Return the 
  return(dat)
  
}

# Clean salaries - generally remove a number of jobs with 
# aberrant salaries from the data read in and, where possible,
# correct some.
cleanSalaries <- function(dat){
  
  # Remove job ALA918 with salary of £2,972,000
  dat<-dat[!grepl("£2,972,000",dat$Salary),]
  
  # Remove job AJL335 which has a salary: £75,249 to £1,014,521 per annum.
  dat<-dat[!grepl("AJL335",dat$JobId),]
  
  # £3,198,606 Plus Living Allowance for a Research Assistant (Early Stage
  # Researcher ESR), Viral Immunology Processing and Vaccine Design ... I think
  # not. Remove using the JobID.
  dat<-dat[!grepl("AMA301",dat$JobId),]
  
  # AMO344 -probably a typoe but have a salary range: £39,000 to £410,000
  dat<-dat[!grepl("AMO344",dat$JobId),]

  # AMM934: salary in Australian dollars directly transcribed to UK pounds.
  dat<-dat[!grepl("AMM934",dat$JobId),]
  
  # These next few cases fix edge-case parsing errors from the jobs2csv.pl
  # script where the wrong salary is picked up from the salary field. 
  # The problems are easier to fix here than to fix in the
  # script itself. Showing the original salary field in a comment.
  
  # £48,743 pro rata to £24,371.50 per annum.
  dat$SalaryMin[dat$JobId=="AJR068"]<-c("£24,371.50")
  dat$SalaryMax[dat$JobId=="AJR068"]<-c("£24,371.50")
  
  # £31,342 (pro rata to £21,939).
  dat$SalaryMin[dat$JobId=="AJH720"]<-c("£21,939")
  dat$SalaryMax[dat$JobId=="AJH720"]<-c("£21,939")
 
  # ANF386: £20,000 which includes a significant industry contribution to the stipend (£5,000)
  dat$SalaryMin[dat$JobId=="ANF386"]<-c("£20,000")
  dat$SalaryMax[dat$JobId=="ANF386"]<-c("£20,000")
  
  # £14,519 equating to an actual salary of £7,955.62 pa for 20 hours per week.
  dat$SalaryMin[dat$JobId=="AKN455"]<-c("£7,955.62")
  dat$SalaryMax[dat$JobId=="AKN455"]<-c("£7,955.62")
  
  # £31,342 (pro rata to £15,671).
  dat$SalaryMin[dat$JobId=="AJO448"]<-c("£15,671")
  dat$SalaryMax[dat$JobId=="AJO448"]<-c("£15,671")
  
  # £13,863 and research costs to a total of £5,000.
  dat$SalaryMin[dat$JobId=="AJN930"]<-c("£13,863")
  dat$SalaryMax[dat$JobId=="AJN930"]<-c("£13,863")
  
  # £1,500 paid directly to the successful student in termly instalments of £500.
  dat$SalaryMin[dat$JobId=="AJJ849"]<-c("£1,500")
  dat$SalaryMax[dat$JobId=="AJJ849"]<-c("£1,500")
  
  # £27,057 p.a., plus a contribution towards University fees to a total of £10,320.
  dat$SalaryMin[dat$JobId=="AKU597"]<-c("£27,057")
  dat$SalaryMax[dat$JobId=="AKU597"]<-c("£27,057")
  
  # £13,500 There will also be additional funds available for research expenses and 
  # conference attendance to the sum of £2,400
  dat$SalaryMin[dat$JobId=="AJN951"]<-c("£13,500")
  dat$SalaryMax[dat$JobId=="AJN951"]<-c("£13,500")
  
  # £39,500 per annum, pro rata (0.5 FTE) to £19,750.
  dat$SalaryMin[dat$JobId=="AKK389"]<-c("£19,750")
  dat$SalaryMax[dat$JobId=="AKK389"]<-c("£19,750")
  
  # £20,374 (pro rata) The advertised salary is equivalent to a rate of pay 
  # of £10.73 per hour.
  dat$SalaryMin[dat$JobId=="AJG538"]<-c("£20,374")
  dat$SalaryMax[dat$JobId=="AJG538"]<-c("£20,374")
  
  # AJG749: has an inconsistency salary. In the header: £1,092,640 and in 
  # the body of the job ad: Starting Salary: £10,926.40 per annum...
  dat$SalaryMin[dat$JobId=="AJG749"]<-c("£10,926.40")
  dat$SalaryMax[dat$JobId=="AJG749"]<-c("£10,926.40")
  
  # Typo in the original data picking up the wrong salary range, fixing.
  dat$SalaryMax[dat$JobId=="ATZ668"]<-c("£24,751")
  dat$SalaryMax[dat$JobId=="ATZ657"]<-c("£37,275")
  
  # Picking up the wrong salaries.
  # AMV891: "£19,573 p.a. for full time post (pro-rated to £15,658 for 0.8 post) + Benefits"
  dat$SalaryMax[dat$JobId=="AMV891"]<-c("£19,573")
  dat$SalaryMin[dat$JobId=="AMV891"]<-c("£15,658")
  
  # ANG797: £21,000 to £210,000.
  # It's a PhD studentship with 21k only.
  dat$SalaryMax[dat$JobId=="ANG797"]<-c("£21,000")
  dat$SalaryMin[dat$JobId=="ANG797"]<-c("£21,000")
  
  # ANJ475: "£13,851 to £175,444 pro rata" for an "Administration Officer - Finance"
  # on a fixed term contract - I think not, removing
  dat<-dat[!grepl("ANJ475",dat$JobId),]
  
  # ANU814: £33,686 to £336,686 per annum, inclusive of London Allowance.
  # The appointment will be on UCL Grade 7.
  dat<-dat[!grepl("ANU814",dat$JobId),]
  
  # Typo in the original AOJ308 remove: "£16,017 to £182,112 per annum"
  dat<-dat[!grepl("AOJ308",dat$JobId),]
  
  # AOE234: "£56,000 FTE, reduced pro-rata to £42,300 at 0.6"
  dat$SalaryMax[dat$JobId=="AOE234"]<-c("£42,300")
  dat$SalaryMin[dat$JobId=="AOE234"]<-c("£42,300")

  # Ignoring the following jobs. Most of these involve incorrect 
  # convertions from one currency to another. For the details see:
  #
  # https://github.com/softwaresaved/jobs-analysis/issues/21
  #
  # Define the problematic jobs:
  badjobs <- c("ALJ907","ALF911","ALD282","ALQ655","ALP859",
               "ALD031","AJQ018","ALI646","AJJ948","AKU020",
               "ALM534","ALF056","AJH830","ALN626","ALJ971",
               "ALF165","ALP599","AKT544","AJN027","AJN606",
               "AJN606","AKB042")
  
  # Remove the corresponding rows.
  dat<-dat[!grepl(paste0(badjobs,collapse="|"),dat$JobId),]
  
  # More bad jobs to remove for mostly the same reasons. For details
  # see:
  #
  # https://github.com/softwaresaved/jobs-analysis/issues/22
  #
  # ALT074 added afterwards. That one has an extra zero in the
  # maximal salary that skes the results.
  badjobs <- c("AJC958","AKF749","ALP173","ALD031","AJR977","AJX048",
              "ALT080","ATS211","ALI646","AKU020","ALM534","ATW506",
              "AKM105","ALJ971","ALF165","ALT074")
  
  # Remove the corresponding rows.
  dat<-dat[!grepl(paste0(badjobs,collapse="|"),dat$JobId),]
  
  return(dat)
  
}

