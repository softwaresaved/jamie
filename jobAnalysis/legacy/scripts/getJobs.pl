#!/usr/bin/perl
#
# Author: Mario Antonioletti (mario@epcc.ed.ac.uk)
#
######################################################################
# Perl script to pull off jobs from www.jobs.ac.uk. Require:
#
# o Perl 5.10 or greater
# o Mojo Perl module (http://mojolicio.us/)
#
# Can install Mojo by running as a privileged user (on a mac add sudo 
# in front of the first line below):
#
# perl -MCPAN -e shell
# install Mojo
# quit
#
# Hopefully all of that should go without a hitch.
# This script works in two phases:
#
# 1. Get a page in www.jobs.ac.uk that lists all the
#    jobs. Can do this by using their search mechanism:
#
#    http://www.jobs.ac.uk/search/?keywords=*&sort=re&s=1&show=10
#
#    Note the show=N at the end. N=10 is good for testing. You
#    can also have N=all which will list all the jobs. The "all"
#    keyword defaults to the maximum per page which is 100. If
#    you look at the search page it will tell you how many jobs
#    they actually have. For now you can put show=4215 or whatever
#    is the current max but I am sure they will get on to this
#    as well.
#
#    One has to get all the job links from this page. Job links are
#    embedded in a piece of html that has:
#
#    <div class="text">
#      <a href="JobRelUrl">Job Name</a>
#      ...
#    </div>
#
#   The JobRelUrl are of the format:
#
#   /job/JobID/JobName
#
#   Need to extract all the JobRelUrl from this page. Collect 
#   all of these.
#  
# 2. Once we have each JobRelUrl we make this into a full URL,
#    visit each URL and extract the job information. The main
#    part of the job details are embedded in a bit of html:
#    
#    <div class="content">
#     ... we want all the stuff that is here ...
#    </div>
#
#   Save this as an html fragment as this contains semantical
#   information that makes it easier for subsequent analysis.
#   Save each fragment as JobID_JobName.
#   
#   Some ads have the type:
#
#   <div id="enhanced-content">
#     ... this stuff does nto follow a generic format so cannot
#         easily parse but we just save these files anyhow.
#   </div>
#
######################################################################

# Let the interpreter warn us of any problems.
use strict;
use warnings;

# Load up the Mojo user agent stuff.
use Mojo::UserAgent;
use Mojo::DOM;

# Use perl 5.10 features.
use v5.10;

# Define the output directory.
my $outdir = "/home/olivier/data/job_analysis/dev_new_parser";

# Create a new user agent.
my $ua = Mojo::UserAgent->new;

# Define the base web site URL.
my $baseurl = "http://www.jobs.ac.uk";

# Keep track of the jobs that have already been downloaded.
my %GotJob;

# Number of jobs available.
my $NumJobs=6000;

# Define the web site URL to operate on.
#my $ws = "$baseurl/search/?keywords=*&sort=re&s=1&show=all";
my $ws = "$baseurl/search/?keywords=*&sort=re&s=1&show=$NumJobs";

##############################################
# First check what job files have already been
# downloaded. Do this by examining what files
# have been downloaded. The file names correspond
# to the job ids.

# Check whether an output job directory exists.
if( -d $outdir){

    # Read existing jobs and keep the job ids.
    print "Directory $outdir already exists.\n";
    print "Collecting information about jobs already downloaded.\n";

    # Get a listing of the files already in the output directory 
    # excluding the "." and ".." directory listings.
    opendir(DIR,$outdir) or 
           die("Could not open the output directory $outdir: $!.\n");
    my @jobs = grep(!/^\./,readdir(DIR));
    closedir(DIR) or 
           die("Could not close the output directory $outdir: $!\n");

    # Now grab the existing job ids
    foreach my $job (@jobs){
      #my($jobid,$name) = split("_",$job);
      #$GotJob{"$jobid"} = 1;  
      $GotJob{"$job"} = 1;  
    }
}else{ # directory does not exist.

    mkdir($outdir) or die("Could not create directory $outdir: $!.\n");
}

##############################################
# Download the jobs.

# Now we start...
print "Downloading new jobs...\n";

# Start a transaction. 
#    Fetch a web site. 
#    Specify to the web server: Do Not Track (DNT).
my $tx = $ua->get($ws => {DNT => 1});

# Set a counter for the number of jobs downloaded.
my $jobcount=1;

# Create a dom object for the page.
my $dom = $tx->res->dom;

# Go to the web site and look for all the bits that have the html:
#
# <div class="text"><a href="JobRelUrl">...</a>...</div>
#
# Extract each JobRelUrl which points to a job.
for my $JobRelUrl ($dom->find("div.text a[href]")->map(attr=>'href')->each){

       # Parse out the jobid and jobname from the JobRelUrl
       # have for path resource the /job/UniqueId/NameForJob
       $JobRelUrl  =~ m^/job/(\w+)/([\w-]+)/^;
       my $jobid   = $1;
       my $jobname = $2;

       # Check that the JobRelUrl is correctly parsed. If this is
       # triggered off then the regular expressions to grab the 
       # jobid and jobname need to be revised.
       if(not defined($jobid) or not defined($jobname)){
           print "WARNING: failed to parse $JobRelUrl correctly.\n";
       }

       # Check whether we already have this job id.
       if(defined $GotJob{"$jobid"}){
	   #print "Already have job $jobid, skipping ...\n";
           next;
       }

       # Create the output filename including the output directory.
       my $outfile = "$outdir/$jobid";

       # Open the output file for this job.
       open(OUT,">",$outfile) or 
                    die("Could not open the output file $outfile: $!.\n");

       # Seem to have utf8 characters so inform Perl to expect this.
       binmode(OUT, ":utf8");

       # Create a new URL from the relative URL.
       my $joburl = "$baseurl"."$JobRelUrl";

       # Now get the job content. 
       # Generate a URL for the job.
       my $w = Mojo::URL->new($joburl);

       # Start a transaction to get the job content.
       #    Specify to the web server: Do Not Track (DNT).
       my $subtx = $ua->get($w => {DNT => 1});

       # Create a dom object for this page.
       my $jdom = $subtx->res->dom;

       # Find out what type of content we have and 
       # print it to file.
       my $content; 

       # An enhanced content page
       if(defined($content = $jdom->at("div#enhanced-content"))){ 
	  print OUT $content;
       }

       # A normal content page.
       if(defined($content=$jdom->at("div.content"))){
              print OUT $content;
       }

       # Close the output file
       close(OUT) or die("Could not close $outfile:$!.\n");

       # Increment the job counter.
       $jobcount++;

} # End loop over $JobRelUrl 

# Seem to overcount by 1 so subract one job.
$jobcount--;

# State how many jobs were downloaded.
print "Downloaded $jobcount jobs from $baseurl.\n\n";

