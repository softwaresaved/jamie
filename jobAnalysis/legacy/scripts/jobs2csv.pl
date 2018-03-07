#!/usr/bin/env perl
#
# Author: Mario Antonioletti (mario@epcc.ed.ac.uk)
#
######################################################################
#
# Perl script that converts job html excerpts downloaded from 
# www.jobs.ac.uk to a CSV file.
#
######################################################################

# Let the interpreter warn us of any problems.
use strict;
use warnings;

# Use switch to deal with degenerate locations.
use Switch;

# Load up the Mojo user agent stuff to do DOM parsing.
use Mojo::DOM;

# Module to read in the entire contents of a file in a oner.
use File::Slurp;

# Require this to output the results in proper CSV format.
use Text::CSV;

# Use perl 5.10 features.
use v5.10;

# Use utf8.
use utf8;

# Print out output in UTF-8 format.
binmode(STDOUT, ":utf8");

# Define whether verbose output is required. If enabled it will print
# out a number of diagnostic messages as the jobs files are being
# processed.
my $quiet = 1;

# The name of the directory where the job files will be read
# from. Also used for the name of the output csv file.
my $outdir = "JobsAcUk";

# Define the output file. Based on the input directory name.
my $outfile = "$outdir".".csv";

# Look-up table in a file used to determine whether a location is in
# the UK.
my $inukfile ="InUK.txt";

# Hash array to store information about the jobs.
my %Jobs;

# File containing known job ids, i.e. ones that have already 
# been processed.
my $knownjobsfile = "knownjobs.txt";
my %knownjob;
my @newjob;
my $appendjobs = 0;

# File to log jobs that are skipped - these are enhanced jobs
# that do not have a regular structure to parse afaik.
my $skippedjobsfile = "skippedjobs.txt";
my %skippedjob;

# Hash array to store information about locations.
my %Locations;

# Hash array to store information about date was job placed.
my %PlacedOn;

# Map calendar months to numbers
my %Month = ("January"=>1, "February"=>2,"March"=>3,"April"=>4,"May"=>5,
             "June"=>6,"July"=>7,"August"=>8,"September"=>9,"October"=>10,
             "November"=>11,"December"=>12);

# Word combinations used to identify software jobs - search is case insensitive
my $sfw_words = "software developer|coding|coder|".
                "research software engineer|software engineer".
                "|programming|programmer".
                "|Fortran|C\\+\\+|Java|JavaScript|Matlab|python|perl";

############################################################
# Check whether a job directory exists which contains all the job
# files that need to be processed.
############################################################
if( -d $outdir){

# Read existing jobs and keep the job ids.
print "Collecting information about jobs already downloaded.\n";

# Get a listing of the files already in the output directory 
# excluding the . and .. directory listings.
opendir(DIR,$outdir) or 
   die("Could not open the output directory $outdir: $!.\n");

# Pull in all the job files in the directory.
my @jobs = grep(!/^\./,readdir(DIR));

# Done, so can close the directory.
closedir(DIR) or 
   die("Could not close the output directory $outdir: $!\n");

# Now grab the existing job ids (equivalent to the file names).
foreach my $job (@jobs){
   my $jobid = $job;
   $Jobs{"$jobid"} = $job;  
}
}else{ # directory does not exist.

   die("No $outdir subdirectory.\n");
}

# Open a file containing a list of jobs already processed, read this
# in. Leave file open and append new jobs.
if(open(JOBIDS,"+<:encoding(UTF-8)",$knownjobsfile) ){ # File already exists
   # Read and then append jobs added.
    $appendjobs = 1;
    while(my $id = <JOBIDS>){
	chomp($id);
	$knownjob{$id}=1;
    }
}else{ # File does not exist. Need to write from scratch.
    open(JOBIDS,">:encoding(UTF-8)",$knownjobsfile) or 
         die("Could not open $knownjobsfile: $!.\n");
    $appendjobs = 0;
}

# Skipped jobs. These are jobs that don't quite fit into
# the general layout, e.g. enhanced jobs.
if(open(SKIP,"+<:encoding(UTF-8)",$skippedjobsfile)){
    while(my $id = <SKIP>){
	chomp($id);
	$skippedjob{$id} = 1;
    }
}else{
    open(SKIP,">:encoding(UTF-8)",$skippedjobsfile) or 
        die("Could not open $skippedjobsfile:$!.\n");
}
    
##########################################################
# Read each of the html job descriptions and extract the
# job information a nested hash identified by the job id
# with the following structure:
#
# JobInfo{job}{"Name"}       Title for the job (first h1 tag).
#             {"Employer"}   The employer.
#             {"Location"}   The location of where the job is based.
#             {"InUK"}        Whether the job is in the UK indicated by 1 or 
#                             not, indicated by a 0.
#             {"SoftwareJob"} Whether the job is a software job as determined
#                             by any of the sfw_words appearing in the ad.
#             {"SoftTermIn"}  Whether software term appears in the titel (T)
#                             the body (B) or not at all.
#             {"Salary"}      Salary field pulled from the job ad.
#             {"SalaryMin"}   Min Salary pulled out from Salary field.
#             {"SalaryMax"}   Max Salary pulled out from Salary field.
#             {"Hours"}       Whether it's full time/part time/etc.
#             {"Contract"}    Whether the job is Contract/Temporary/Permanent.
#             {"Funding for"} Who the funding is for (qualifications).
#             {"Qualification type"} Information if a qualification.
#             {"Placed on"}   When the job ad came on-line.
#             {"Closes"}      Whent the job application closes.
#             {"Job Ref"}     The job reference.
#             {"h1"}          Populate if there are h1 headings.
#             {"h2"}          Populate if there are h2 headings.
#             {"h3"}          Populate if there are h3 headings.
#             {"Description"} Description of the job.
#             {"Type/Role"}   Role or type of job.
#             {"SubjectArea"} Semicolon delimited list of the subject areas
#                             a job can be classied under.
#             {"Location2"}   A second location classification.
#
###########################################################
my %JobInfo;

# Fields we intend to extract.
my %knownfield= (
                "Location"=>1,
                "Salary"=>1,
                "Funding amount" => 1, # Mapped to Salary
                "Hours"=>1,
                "Contract"=>1,
                "Funding for"=>1,
                "Qualification type"=>1,
                "Placed on"=>1,
                "Closes"=>1,      
                "Expires"=>1,          # Mappled to Closes
                "Job Ref"=>1,
                "Reference"=>1         # Mapped to Job Ref
               );

# Count the files/jobs processed.
my $count=1;

# Count the number of software jobs.
my $softcount = 0;

# Look-up table to indicate whether a location is in the UK or not.
my %InUK;

# Array to store any unknown locations, i.e. whether they are 
# in the UK or not.
my %UnknownLocations;

# Read look-up table determining whether locations are in the UK or
# not (semicolon delimited file - location is in the UK by 1 or not
# with a 0).
open(INUKFILE,"<:encoding(UTF-8)",$inukfile) or 
     die("Could not open the $inukfile: $!.\n");

while(my $line=<INUKFILE>){
     chomp($line);                       # Remove new line.
     my($place,$inuk)=split(";",$line);  # Split on the semicolon.
     $InUK{$place}=$inuk;                # Store lookup table.
}
close(INUKFILE) or die("Could not close $inukfile: $!.\n");

# Count the number of jobs skipped - skipping featured jobs 
# as the content structure of these is different. Their ehanced
# content is free flowing - cannot pull stuff out.
my $skippedjobs = 0;

# Print out information.
print "Processing jobs ...\n";

# Currency regular expression
# ([£€¥]\d([\d,]+)?(\.\d+))
my $cur = '(£\s*\d([\d,]+)?(\.\d+)?)';

# Loop over the jobs ids.
foreach my $job (keys(%Jobs)){

    # Skip if we already known or previously skipped.
    next if($knownjob{$job} or $skippedjob{$job});

    # Open the job file.
    my $infile="$outdir/$Jobs{$job}";

    # Slurp the whole contents of the job into a dom object.
    my $contents = read_file($infile, binmode  => ":encoding(utf8)");
    my $dom      = Mojo::DOM->new->parse($contents );

    # Some of the job files (featured jobs) have enhanced-content ids
    # which require a different processing model to the standard jobs.
    if(not defined($dom->find("div.section")->[1])){
	print "Cannot process $job skipping.\n" if(not $quiet);
	print SKIP "$job\n";
        $skippedjobs++;
        next;
    }

    # Print to screen what we are processing if in verbose mode.    
    print "*** Processing (",$count,"): $job\n" if(not $quiet);

    # This is a new job.
    push(@newjob,$job);
    
    # Updated the number of jobs processed counter.
    $count++;

    # Defaults for software jobs, i.e. not a software job
    $JobInfo{$job}{"SoftwareJob"} = 0;
    $JobInfo{$job}{"SoftTermIn"}  = "N";

    # Get the job title from the first h1 heading.
    $JobInfo{$job}{"Name"} = $dom->at("h1")->text;
    if($JobInfo{$job}{"Name"} =~ /$sfw_words/i){
       $JobInfo{$job}{"SoftwareJob"}=1;
       $JobInfo{$job}{"SoftTermIn"}="T";
       #print $dom->find("h1")->text,"\n";
    }

    # Get the employer info for the job. Only expect one of these.
    $JobInfo{$job}{"Employer"}=
       $dom->find("div.section a[href^=/employer/]")->map(attr=>"href")->each;

    # Check that we have an employer.
    if(not defined($JobInfo{$job}{"Employer"})){
       print "Undefined employer for job $job.\n";
       print $dom->find("div.section a[href^=/employer/]"),"\n";
       exit;
    }

    # Remove the beginning of the path for the employer.
    $JobInfo{$job}{"Employer"} =~ s:/employer/::;

    # Loop over an html table to grab:
    #
    #                  Location, 
    #                  Salary or Funding Amount -> Salary, 
    #                  Hours, 
    #                  Contract,
    #                  Contract Type -> Contract,
    #                  Placed on, 
    #                  Closes or Expires -> Closes,
    #                  Job Ref or References -> Job Ref
    #   
    for my $row ($dom->find("table.advert-details tr")->each){

        # Skip any rows that just have a colspan
        next if($row =~ m:<td colspan="2">:);

        # Pick up all the data points by separating row elements by
	# a colon.
	my $row_cont = $row->all_text;
	$row_cont    =~ s/\s+/ /g;                # Remove extra spaces
        my($label,$data) = split(":",$row_cont); # Split on the colon
	$label =~ s/^\s+|\s+$//g;        # trim leading and trailing spaces
        $data  =~ s/^\s+|\s+$//g if(defined($data));

        # Skip the row if we cannot identify a label.
        next if($label eq "" || not defined($label));

	# Remove the colon from the label
	# $label =~ s/://;

	# Map Funding amount to Salary
	if($label =~ /Funding amount/){ $label = "Salary"}
	
        # Map Contract Type to Contract in the context of the advert
        # details they are used synonimously. There is another
        # "Contract Type" which gives the length of the contract.
	if($label =~ /Contract Type/){ $label = "Contract"}

	# Check that we know of this label. Track of any unknown
	# labels.
	if(not defined($knownfield{$label})){
	    $knownfield{$label}=0;
	}

	# Take "Reference" as an alias for "Job Ref".
	if($label =~ /Reference/){
	   $label = "Job Ref";
	}
	
        # Process info about when the job was placed.
        if($label =~ /Placed on/){

           # Parse the date
           $data =~ /(\d+)\w+ (\w+) (\d+)/;
           my $d = $1;
           my $m = $Month{$2};
           my $y = $3;
           $data = "$d/$m/$y";
    
           if(not defined($PlacedOn{$data})){
              $PlacedOn{$data}=1;
           }else{
              $PlacedOn{$data}++;
           }
        }

        # Process info about when the job closes.
        if($label =~ /Closes|Expires/){
	    
           # Parse the date
           $data =~ /(\d+)\w+ (\w+) (\d+)/;
           my $d = $1;
           my $m = $Month{$2};
           my $y = $3;
           $data = "$d/$m/$y";
	   
	   # change the label to Closes (in case it 
           # had Expires).
	   $label = "Closes";
        }

        # Process location information.
        if($label =~ /Location/){

           # Store location.
           if(not defined($Locations{"$data"})){
              $Locations{"$data"} =1;
           }else{
              $Locations{"$data"}++;
           }

           # Determining whether the locations is in the UK.
           if(defined($InUK{$data})){ # Do we know of this location
              $JobInfo{$job}{"InUK"} = $InUK{$data};
           }else{
              $JobInfo{$job}{"InUK"} = "Unknown";
              $UnknownLocations{$data}= "$job";
           }
        }

        # Process Salary field into various types.
        if($label =~ /Salary/){
            
           # Count the number of "to"s that occur in the data string.
           my $nto = ($data =~ s/ to / to /g);
           $nto = ($nto eq "")?0:$nto;

           # Count the number of times a pound sign occurs in the
           # string.
           my $npounds = ($data =~ s/£/£/g);
           $npounds = ($npounds eq "")?0:$npounds;

	   # Substitute any ks for thousands
	   $data =~ s/(£\d([\d,]+)?(.\d+)?)k/$1,000/ig;
	   
	   # A crazy edge case piece of notation sometimes used.
	   if($data =~ /£\d+\.\d,000/){
	       # Can't seem to do $200 so using a two phase subst.
               $data =~ s/(£[\d,]+)\.(\d),000/$1,$2aaaaaa/g;
	       $data =~ s/aaaaaa/00/g;
	   }
	   
           # Process the data. 
           if(($data =~ /not specified/i && $npounds == 0 )|| $data =~ /£Main/){   
              $JobInfo{$job}{"SalaryMin"}="Unspecified";
              $JobInfo{$job}{"SalaryMax"}="Unspecified";           
           }elsif($data =~ /Up to|hourly rate|per hour/i  &&   $npounds > 1 ){
	      # Pick the first salary.
	      $data =~ /$cur/;
              my $sal = $1;
	      $JobInfo{$job}{"SalaryMin"}="$sal";
              $JobInfo{$job}{"SalaryMax"}="$sal";
           }elsif($data =~ /Up to|per hour|per annum|hourly rate/i && 
              $npounds == 1){  # Max salary
              $data =~ /$cur/;
              my $sal = $1;
              if(not defined($sal)){
                 print "Undefined salary:\n";
                 print "\t$job: $data.\n";
                 $JobInfo{$job}{"SalaryMin"}="Unspecified";
                 $JobInfo{$job}{"SalaryMax"}="Unspecified";           
              }else{
                 $JobInfo{$job}{"SalaryMin"}="$sal";
                 $JobInfo{$job}{"SalaryMax"}="$sal";
              }
           }elsif(#$npounds == 0 &&
              $data =~ /negotiable|competitive|professorial
                       |commensurate/ix){ # Various
              $JobInfo{$job}{"SalaryMin"}="Negotiable";
              $JobInfo{$job}{"SalaryMax"}="Negotiable";
           }elsif(($npounds == 0||$data =~ /£\s*Competitive/i)  &&
              $data =~ /specified|funded|advert|RCUK
                        |Hourly|Attractive|Senior|
                         |comprehensive|package|8b/ix){ # Unspecified
              $JobInfo{$job}{"SalaryMin"}="Unspecified";
              $JobInfo{$job}{"SalaryMax"}="Unspecified";           
           }elsif($nto == 1 && $npounds == 2 && $data =~ / to /){ 
              # From to salary
              my($start,$end) = split(" to ",$data);

              $start =~ /$cur/;
              $start = $1;
              $end   =~ /$cur/;
              $end   = $1;
              if(not defined($start) || not defined($end)){
                 print "Undefined salary start/end for job $job.\n";
                 print "\t$job: $data.\n";
                 $JobInfo{$job}{"SalaryMin"}="Unspecified";
                 $JobInfo{$job}{"SalaryMax"}="Unspecified";           
              }else{
                 $JobInfo{$job}{"SalaryMin"}="$start";
                 $JobInfo{$job}{"SalaryMax"}="$end";
              }
           }elsif($nto >= 1 && $npounds > 1 &&
                 $data =~ /.*$cur\s+to\s+$cur.*/){
                 my $start = $1;
                 my $end   = $4;
                 $JobInfo{$job}{"SalaryMin"}="$start";
                 $JobInfo{$job}{"SalaryMax"}="$end";
           }elsif($data =~ /$cur/){  # Single salary
                 my $salary = $1;
                 $JobInfo{$job}{"SalaryMin"}=$salary;
                 $JobInfo{$job}{"SalaryMax"}=$salary;
           }elsif($data =~ /£Attractive/i){
                 $JobInfo{$job}{"SalaryMin"}="Unspecified";
                 $JobInfo{$job}{"SalaryMax"}="Unspecified";
          }elsif($data =~ /stipend/i){
	         # pick out the first salary as the stipend.
                 $data =~ /([£€]\d([\d,]+)?(.\d+)?)/;  
                 my $salary = $1;   
                 $JobInfo{$job}{"SalaryMin"}=$salary;
                 $JobInfo{$job}{"SalaryMax"}=$salary; 
            }elsif($data =~ /.*$cur\s*\-\s*$cur.*/){
                 my $start = $1;
                 my $end   = $4;
                 $JobInfo{$job}{"SalaryMin"}="$start";
                 $JobInfo{$job}{"SalaryMax"}="$end";	          
	    }elsif($nto == 0 && $npounds == 2){
		 $data =~ /.*$cur.*$cur.*/;
                 my $start = $1;
                 my $end   = $4;
                 $JobInfo{$job}{"SalaryMin"}=$start;
                 $JobInfo{$job}{"SalaryMax"}=$end; 
           }else{                                        #  Unknown
                 $JobInfo{$job}{"SalaryMin"}="Unknown";
                 $JobInfo{$job}{"SalaryMax"}="Unknown";   	       
                 print "Unknown Salary type ($job): $data.\n";
                 print "\t$job: $data.\n";
                 #exit;
           }
         
        }

        # Check whether there is a problem.
        if(not defined($label) or not defined($data)){
           print "Problem processing job $job.\n";
           print "Could not pick up data in:\n $row\n\n";
           exit;
        }


        # Add to the information collected.
        $JobInfo{$job}{$label} = $data;
        #print "$label -> $data\n";

    } # End for loop over the table element

    # Pull in the additional information from an inline box which 
    # generally has the format below. There will be each of these
    # segments - a title consisting of a location, subject area and
    # a type/role. The content is in a div of class j-nav-pill-box
    # and it may be a series of links or values. A location will
    # just have another p pairing. So for "Subject Area(s):" and
    # "Type / Role:" we have:
    #
    #  <div class="inlineBox">
    #    <p>Title:</p>
    #    <div class="j-nav-pill-box">
    #      <a class="j-nav-pill-box__link j-nav-pill-box__link--label \
    #              j-nav-pill-box__link--highlight" 
    #             href="/jobs/administrative">Administrative</a>*
    #    </div>
    #  </div>
    #
    # For location we have:
    #
    # <div class="inlineBox">
    #    <p>Location(s):</p>
    #    <p>Place</p>
    # </div>
    #
    # From this we get:
    #                     Location2
    #                     Subject Area
    #                     Type / Role
    #
    for my $item ($dom->find("div.inlineBox")->each){

	# Use variables for the title and contents.
	my ($title,$cont);

        # Ignore if there are no <p>...</p> children.
	next if(!defined($item->find("p")->[0]) ||
                    $item->find("p")->map("all_text")->[0] eq "");

	# First <p>...</p> gives the title.
	$title = $item->find("p")->map("all_text")->[0];

	# Grab the data that is of interest.
	if($title =~ /Location/){
	    # Rename the title	
	    $title = "Location2";

            # Find all the <p> elements, convert to text, trim leading and trailing spaces.
            # trim routine from: https://perlmaven.com/trim
	    my @locs = ($item->find("p")->map("all_text")
                                        ->map( sub { my $s = shift; $s =~ s/^\s+|\s+$//g; return $s } )
                                        ->each
                       );

	    # Junk the first element which is just the title again.
	    shift(@locs);
            # No grab the content
	    $cont = join(";",@locs);

        }elsif($title =~ /Subject/){
            $title = "Subject Area";
	    $cont=join(";",$item->find("a")->map("all_text")
                                           ->map( sub {my $s = shift; $s =~ s/^\s+|\s+$//g; return($s)} )
                                           ->each);
        }elsif($title =~ /Type/){
	    $title = "Type/Role";
	    $cont=join(";",$item->find("a")->map("all_text")
                                           ->map( sub {my $s = shift; $s =~ s/^\s+|\s+$//g; return($s)} )
                                           ->each);
        }else{
	    print "Unknown field: \"$title\".\n";
	    exit;
	}
	
       # Get rid of any new lines.
       chomp($title);

       # Remove the semicolon and any spaces
       $title =~ s/://;
       $title =~ s/ //g;

       # Store the new information.
       $JobInfo{$job}{$title}=$cont;
    }
    
    # Collect information about the h1, h2 and h3 headers if present.
    $JobInfo{$job}{"h1"}=join(";",$dom->find("h1")->map("all_text")->each);
    $JobInfo{$job}{"h2"}=join(";",$dom->find("h2")->map("all_text")->each);
    $JobInfo{$job}{"h3"}=join(";",$dom->find("h3")->map("all_text")->each);

    # Obtain a description of the job
    $JobInfo{$job}{"Description"}=
                    $dom->find("div.section")->[1]->all_text();

    if($JobInfo{$job}{"Description"} =~ /$sfw_words/i){
       $JobInfo{$job}{"SoftwareJob"}=1;
       if($JobInfo{$job}{"SoftTermIn"} =~ /T/){
          $JobInfo{$job}{"SoftTermIn"} .= "B";
       }else{
          $JobInfo{$job}{"SoftTermIn"} = "B";
       }
    }

    # Deal with degenerate locations.
    switch($JobInfo{$job}{"Location"}){
	case "Perth"     {if($JobInfo{$job}{"Location2"} eq "Australasia"){
                   	     $JobInfo{$job}{"InUK"} = 0;
                          }
	}
	case "Newcastle" {if($JobInfo{$job}{"Location2"} eq "Australasia"){
                   	     $JobInfo{$job}{"InUK"} = 0;
                          }
	}
	case "Boston"    {if($JobInfo{$job}{"Location2"} eq 
                                                "South East England"){
                   	     $JobInfo{$job}{"InUK"} = 1;
                          }
	}
        case "Hawthorn"  {if($JobInfo{$job}{"Location2"} eq
                                                "South West England"){
                             $JobInfo{$job}{"InUK"} = 1;
                          }
        }
        case undef       {if($JobInfo{$job}{"Location2"} =~ 
                          /England|Scotland"Northern Ireland|London|Wales/){
                   	     $JobInfo{$job}{"InUK"} = 1;	    
                           }
        }
	
    } # End switch

    # Count the number of software jobs.
    $softcount++ if($JobInfo{$job}{"SoftwareJob"});

    #exit;

} # End loop over jobs.

################################################
# Find out if there are any fields that are not
# being picked up.

print "\n";
foreach my $f (keys(%knownfield)){

    if($knownfield{$f} == 0){
	print "Have a fild: \"$f\" that is not being recorded.\n";
    }

}

###############################################################
# If we picked up any new jobs append these to the known jobs 
# file unless it is not known whether it is in the UK - we want
# to fix the look-up-table and rerun this script.
if(scalar @newjob > 0){
   foreach my $jid (@newjob){

      # Skip jobs that do have the InUK defined, eg enhanced jobs
      # that are currently not being processed.
      next if(not defined($JobInfo{$jid}{"InUK"}));

      # Skip jobs of unknown locations.
      next if($JobInfo{$jid}{"InUK"} eq "Unknown");

      print JOBIDS "$jid\n";
  }

}

# Close the known files.
close(JOBIDS) or die("Problems closing $knownjobsfile: $!.\n");
close(SKIP)   or die("Problems closing $skippedjobsfile: $!.\n");

#########################################
# Now write all the data into a CSV file.
#########################################

# Get the job ids
my @jobs = keys(%JobInfo);

#print join("\n",keys(%{$JobInfo{$jobs[0]}})),"\n";
#exit;

# Open the csv output file Append if we have skipped known job ids
# otherwise clobber the existing file.
if($appendjobs == 1){

   open(OUTFILE,">>:encoding(utf8)",$outfile) 
                or die("Could not open $outfile: $!\n");
}else{ 
 
   open(OUTFILE,">:encoding(utf8)",$outfile) 
                or die("Could not open $outfile: $!\n");
}

# Create a csv object handle.
my $csv = Text::CSV->new ( { binary => 1, eol => "\r\n" } )  
         or die("Cannot use CSV: ".Text::CSV->error_diag ());

# Compse the column headings.
my @header =( "JobId",
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
	      "QualificationType",	      
              "PlacedOn",
              "Closes",
              "JobRef",
              "h1",
              "h2",
              "h3",
	      "TypeRole",
	      "SubjectArea",
	      "Location2",
              "Description" 
      );

# Print the headers to file if not appending jobs.
my $stat = $csv->print(\*OUTFILE,\@header) if(! $appendjobs);

# Now loop over the jobs and output the contents to csv
foreach my $job (@jobs){

   # Push content into this array.
   my @row = ();

   # Don't write any jobs if the InUK field is not known.
   next if($JobInfo{$job}{"InUK"} eq "Unknown");

   # Push the row data into an array.
   push(@row,$job);
   push(@row,$JobInfo{$job}{"Name"});
   push(@row,$JobInfo{$job}{"Employer"});  
   push(@row,$JobInfo{$job}{"Location"});
   push(@row,$JobInfo{$job}{"InUK"});
   push(@row,$JobInfo{$job}{"SoftwareJob"});
   push(@row,$JobInfo{$job}{"SoftTermIn"});
   push(@row,$JobInfo{$job}{"Salary"});
   push(@row,$JobInfo{$job}{"SalaryMin"});
   push(@row,$JobInfo{$job}{"SalaryMax"});
   push(@row,$JobInfo{$job}{"Hours"});
   push(@row,$JobInfo{$job}{"Contract"});
   push(@row,$JobInfo{$job}{"Funding for"});  
   push(@row,$JobInfo{$job}{"Qualification type"});  
   push(@row,$JobInfo{$job}{"Placed on"});
   push(@row,$JobInfo{$job}{"Closes"});   
   push(@row,$JobInfo{$job}{"Job Ref"});  
   push(@row,$JobInfo{$job}{"h1"}); 
   push(@row,$JobInfo{$job}{"h2"});      
   push(@row,$JobInfo{$job}{"h3"});
   push(@row,$JobInfo{$job}{"Type/Role"});      
   push(@row,$JobInfo{$job}{"SubjectArea"});
   push(@row,$JobInfo{$job}{"Location2"});      
   push(@row,$JobInfo{$job}{"Description"}); 

   # Write the row to file.
   $stat = $csv->print(\*OUTFILE,\@row);   
}

# Finished with the output file.
close(OUTFILE) or die("Could not close $outfile: $!#n");

# Over counted by one job
$count--;

# Print out the number of jobs skipped
print "\n\nProcessed $count new jobs. $softcount software jobs identified. ",
      "$skippedjobs jobs were skipped.\n\n";

# Print out if there any unknown locations
if(scalar( keys(%UnknownLocations)) > 0){

    print "\n\nThese unknown locations have been appended to the $inukfile ",
          "file please specify whether they are in the UK or not.\n\t";

    # Open the file to append to
    open(FH,">>:encoding(UTF-8)",$inukfile) or 
             die("Could not open $inukfile to append to: $!.\n");

    foreach my $k (keys(%UnknownLocations)){

          # Print to standard output.
          print "\n\t $k ($UnknownLocations{$k})";

          # Print to file.
          print FH "$k;\n";

    }
    print "\n\n";
    
    close(FH) or die("Could not close the $inukfile: $!\n");

}

